/**
 * 图谱时间解析与范围计算（抽离自 App.vue）
 * 设计为纯函数：不直接读写 Vue ref。
 */

/**
 * 解析一条 link 的时间属性为 [startDate, endDate]
 * @param {Object} link
 * @param {Record<string, {start: string|number|Date, end: string|number|Date}>} timePeriodMap
 * @returns {[Date|null, Date|null]}
 */
export function normalizeLinkTime(link, timePeriodMap = {}) {
  const properties = link?.properties || {};
  let dateString = properties.time_start || properties.time_end || properties.time_value;
  let startDate = null;
  let endDate = null;

  if (dateString) {
    const matchYearMonth = String(dateString).match(/(\d{4})年(\d{1,2})月/);
    const matchYear = String(dateString).match(/(\d{4})年/);

    if (matchYearMonth) {
      const year = parseInt(matchYearMonth[1]);
      const month = parseInt(matchYearMonth[2]);
      startDate = new Date(year, month - 1, 1);
      endDate = new Date(year, month, 0);
    } else if (matchYear) {
      const year = parseInt(matchYear[1]);
      startDate = new Date(year, 0, 1);
      endDate = new Date(year, 11, 31);
    }

    if (properties.time_start && properties.time_end) {
      const startMatch = String(properties.time_start).match(/(\d{4})年(\d{1,2})月?/);
      const endMatch = String(properties.time_end).match(/(\d{4})年(\d{1,2})月?/);
      if (startMatch) {
        const year = parseInt(startMatch[1]);
        const month = startMatch[2] ? parseInt(startMatch[2]) : 1;
        startDate = new Date(year, month - 1, 1);
      }
      if (endMatch) {
        const year = parseInt(endMatch[1]);
        const month = endMatch[2] ? parseInt(endMatch[2]) : 12;
        endDate = endMatch[2] ? new Date(year, month, 0) : new Date(year, 11, 31);
      }
    }
  }

  if (!startDate && !endDate) {
    if (properties.time_start && properties.time_end) {
      startDate = new Date(properties.time_start);
      endDate = new Date(properties.time_end);
    } else if (properties.time_value) {
      const timeVal = String(properties.time_value);
      if (timeVal.match(/^\d{4}-\d{2}$/)) {
        startDate = new Date(timeVal + '-01');
        endDate = new Date(startDate.getFullYear(), startDate.getMonth() + 1, 0);
      } else {
        startDate = new Date(timeVal);
        endDate = new Date(timeVal);
      }
    } else if (properties.time_period && timePeriodMap?.[properties.time_period]) {
      const period = timePeriodMap[properties.time_period];
      startDate = new Date(period.start);
      endDate = new Date(period.end);
    }
  }

  startDate = isNaN(startDate?.getTime()) ? null : startDate;
  endDate = isNaN(endDate?.getTime()) ? null : endDate;

  if (startDate && !endDate) {
    endDate = new Date(startDate);
    endDate.setDate(startDate.getDate() + 1);
  }
  if (endDate && !startDate) {
    startDate = new Date(endDate);
    startDate.setDate(endDate.getDate() - 1);
  }

  return [startDate, endDate];
}

/**
 * 计算图谱全局日期范围
 * @param {Array} links
 * @param {{minFallback?: Date, maxFallback?: Date, timePeriodMap?: any}} opts
 * @returns {{minDate: Date, maxDate: Date, selectedRange: [Date, Date]}}
 */
export function computeGraphDateRange(links, opts = {}) {
  const {
    minFallback = new Date('1941-01-01'),
    maxFallback = new Date('1945-10-01'),
    timePeriodMap = {},
  } = opts;

  let tempMinDate = null;
  let tempMaxDate = null;

  (links || []).forEach((link) => {
    const [linkStart, linkEnd] = normalizeLinkTime(link, timePeriodMap);
    if (linkStart && (!tempMinDate || linkStart < tempMinDate)) tempMinDate = linkStart;
    if (linkEnd && (!tempMaxDate || linkEnd > tempMaxDate)) tempMaxDate = linkEnd;
  });

  const minDate = tempMinDate && tempMaxDate ? tempMinDate : minFallback;
  const maxDate = tempMinDate && tempMaxDate ? tempMaxDate : maxFallback;

  return { minDate, maxDate, selectedRange: [minDate, maxDate] };
}

