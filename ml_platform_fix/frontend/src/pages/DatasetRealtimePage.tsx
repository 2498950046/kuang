import { FormEvent, useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Database, History, UploadCloud } from 'lucide-react'
import { toast } from 'sonner'
import { MLMobileNav, MLSidebar } from '@/components/ml-sidebar'
import { Card } from '@/components/ui/card'
import { apiDelete, apiGet, apiPostForm, apiPostJson } from '@/lib/api'

type Histogram = { bin_edges: number[]; counts: number[] }
type NumericProfile = { name: string; histogram: Histogram }
type ScatterPoint = { x: number; y: number }
type ScatterPlot = { x_col: string; y_col: string; points: ScatterPoint[] }
type CorrHeatmap = { columns: string[]; matrix: Array<Array<number | null>> }
type PcaPoint = { x: number; y: number }
type PcaProjection = { explained_variance_ratio: number[]; points: PcaPoint[] }
type Analysis = {
  scatter_plot: ScatterPlot | null
  corr_heatmap: CorrHeatmap | null
  pca_projection: PcaProjection | null
}

type DatasetPreview = {
  row_count: number
  profiled_rows: number
  columns: string[]
  numeric_columns: NumericProfile[]
  id_like_columns: string[]
  analysis: Analysis
  sample_rows: Array<Record<string, string>>
}

type DatasetRecord = {
  id: string
  name: string
  description: string
  filename: string
  samples: number
  features: number
  columns: string[]
  size: string
  created_at: string
  status: string
}

type UploadDatasetResponse = { dataset: DatasetRecord; preview: DatasetPreview }
type DatasetPreviewResponse = UploadDatasetResponse
type DatasetListResponse = { datasets: DatasetRecord[] }
type DatasetDeleteResponse = { ok: boolean; dataset_id: string }
type DatasetBatchDeleteResponse = { ok: boolean; deleted_count: number; dataset_ids: string[] }
type DatasetRowsResponse = {
  total: number
  offset: number
  limit: number
  rows: Array<Record<string, string>>
}

type AnalysisTab = 'hist' | 'scatter' | 'corr' | 'pca'
const DEFAULT_PAGE_SIZE = 15

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : []
}

function cleanLabel(text: string): string {
  return String(text ?? '')
    .replace(/\ufffd/g, '')
    .replace(/[\u0000-\u001f]+/g, '')
    .replace(/\u00b5/g, 'u')
    .replace(/m虏/g, 'm2')
    .replace(/m²/g, 'm2')
    .replace(/\s+/g, ' ')
    .trim()
}

function shortLabel(text: string, max = 16): string {
  const cleaned = cleanLabel(text)
  return cleaned.length > max ? `${cleaned.slice(0, max)}...` : cleaned
}

function normalizePreview(raw: unknown): DatasetPreview {
  const obj = (raw ?? {}) as Record<string, unknown>
  const analysisRaw = (obj.analysis ?? {}) as Record<string, unknown>
  return {
    row_count: Number(obj.row_count ?? 0),
    profiled_rows: Number(obj.profiled_rows ?? 0),
    columns: asArray<string>(obj.columns),
    numeric_columns: asArray<NumericProfile>(obj.numeric_columns),
    id_like_columns: asArray<string>(obj.id_like_columns),
    analysis: {
      scatter_plot: (analysisRaw.scatter_plot ?? null) as ScatterPlot | null,
      corr_heatmap: (analysisRaw.corr_heatmap ?? null) as CorrHeatmap | null,
      pca_projection: (analysisRaw.pca_projection ?? null) as PcaProjection | null,
    },
    sample_rows: asArray<Record<string, string>>(obj.sample_rows),
  }
}

export default function DatasetRealtimePage() {
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)

  const [history, setHistory] = useState<DatasetRecord[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [selectedHistoryIds, setSelectedHistoryIds] = useState<string[]>([])

  const [result, setResult] = useState<UploadDatasetResponse | null>(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState('')
  const [selectedNumericCol, setSelectedNumericCol] = useState('')
  const [analysisTab, setAnalysisTab] = useState<AnalysisTab>('hist')

  const [tableRows, setTableRows] = useState<Array<Record<string, string>>>([])
  const [tableOffset, setTableOffset] = useState(0)
  const [tableTotal, setTableTotal] = useState(0)
  const [loadingRows, setLoadingRows] = useState(false)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [pageSizeInput, setPageSizeInput] = useState(String(DEFAULT_PAGE_SIZE))
  const [jumpPageInput, setJumpPageInput] = useState('1')

  const totalPages = useMemo(() => Math.max(1, Math.ceil((tableTotal || 0) / pageSize)), [tableTotal, pageSize])
  const currentPage = useMemo(() => Math.floor(tableOffset / pageSize) + 1, [tableOffset, pageSize])
  const allHistorySelected = history.length > 0 && selectedHistoryIds.length === history.length

  useEffect(() => setJumpPageInput(String(currentPage)), [currentPage])

  const refreshHistory = async () => {
    setHistoryLoading(true)
    try {
      const data = await apiGet<DatasetListResponse>('/api/datasets')
      const rows = data.datasets ?? []
      setHistory(rows)
      setSelectedHistoryIds((prev) => prev.filter((id) => rows.some((r) => r.id === id)))
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载历史数据集失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  useEffect(() => {
    void refreshHistory()
  }, [])

  const loadRows = async (datasetId: string, offset: number, customPageSize?: number) => {
    const size = customPageSize ?? pageSize
    setLoadingRows(true)
    try {
      const data = await apiGet<DatasetRowsResponse>(`/api/datasets/${datasetId}/rows?offset=${Math.max(0, offset)}&limit=${Math.max(1, Math.min(size, 2000))}`)
      setTableRows(data.rows ?? [])
      setTableOffset(data.offset ?? 0)
      setTableTotal(data.total ?? 0)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载样例数据失败')
    } finally {
      setLoadingRows(false)
    }
  }

  const applyResult = async (resp: UploadDatasetResponse) => {
    const normalized = normalizePreview(resp.preview)
    const next = { dataset: resp.dataset, preview: normalized }
    setResult(next)
    setSelectedDatasetId(resp.dataset.id)
    setPageSize(DEFAULT_PAGE_SIZE)
    setPageSizeInput(String(DEFAULT_PAGE_SIZE))
    setTableTotal(normalized.row_count)
    setTableOffset(0)
    setSelectedNumericCol(normalized.numeric_columns[0]?.name ?? '')
    await loadRows(resp.dataset.id, 0, DEFAULT_PAGE_SIZE)
  }

  const selectDataset = async (datasetId: string) => {
    try {
      const resp = await apiGet<DatasetPreviewResponse>(`/api/datasets/${datasetId}/preview?sample_limit=${DEFAULT_PAGE_SIZE}`)
      await applyResult(resp)
      toast.success(`已加载数据集：${resp.dataset.name}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '加载数据集失败')
    }
  }

  const onDeleteDataset = async (dataset: DatasetRecord) => {
    if (!window.confirm(`确定删除数据集“${dataset.name}”吗？此操作不可恢复。`)) return
    try {
      await apiDelete<DatasetDeleteResponse>(`/api/datasets/${dataset.id}`)
      if (selectedDatasetId === dataset.id) {
        setSelectedDatasetId('')
        setResult(null)
        setTableRows([])
        setTableOffset(0)
        setTableTotal(0)
      }
      setSelectedHistoryIds((prev) => prev.filter((id) => id !== dataset.id))
      await refreshHistory()
      toast.success(`已删除数据集：${dataset.name}`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '删除数据集失败')
    }
  }

  const toggleHistorySelect = (id: string) => {
    setSelectedHistoryIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const toggleSelectAllHistory = () => {
    if (allHistorySelected) {
      setSelectedHistoryIds([])
      return
    }
    setSelectedHistoryIds(history.map((x) => x.id))
  }

  const onBatchDelete = async () => {
    if (selectedHistoryIds.length === 0) {
      toast.error('请先选择要删除的数据集')
      return
    }
    if (!window.confirm(`确定批量删除 ${selectedHistoryIds.length} 个数据集吗？此操作不可恢复。`)) return
    try {
      const resp = await apiPostJson<DatasetBatchDeleteResponse>('/api/datasets/batch-delete', { dataset_ids: selectedHistoryIds })
      const deleted = new Set(resp.dataset_ids ?? [])
      if (result && deleted.has(result.dataset.id)) {
        setSelectedDatasetId('')
        setResult(null)
        setTableRows([])
        setTableOffset(0)
        setTableTotal(0)
      }
      setSelectedHistoryIds([])
      await refreshHistory()
      toast.success(`批量删除完成：${resp.deleted_count} 个`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '批量删除失败')
    }
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!file) {
      toast.error('请先选择 CSV 或 ZIP 文件')
      return
    }
    const fd = new FormData()
    fd.append('file', file)
    if (name.trim()) fd.append('name', name.trim())
    if (description.trim()) fd.append('description', description.trim())
    setUploading(true)
    try {
      const resp = await apiPostForm<UploadDatasetResponse>('/api/datasets/upload', fd)
      await applyResult(resp)
      await refreshHistory()
      toast.success('上传成功，数据集已保存到数据库')
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '上传失败')
    } finally {
      setUploading(false)
    }
  }

  const onApplyPageSize = async () => {
    if (!result) return
    const parsed = Number(pageSizeInput)
    if (!Number.isFinite(parsed) || parsed <= 0) {
      toast.error('每页条数请输入大于 0 的数字')
      return
    }
    const clamped = Math.max(1, Math.min(Math.floor(parsed), 2000))
    setPageSize(clamped)
    await loadRows(result.dataset.id, 0, clamped)
  }

  const onJumpPage = async () => {
    if (!result) return
    const parsed = Number(jumpPageInput)
    if (!Number.isFinite(parsed) || parsed <= 0) {
      toast.error('页码请输入大于 0 的数字')
      return
    }
    const page = Math.min(Math.max(1, Math.floor(parsed)), totalPages)
    await loadRows(result.dataset.id, (page - 1) * pageSize)
  }

  const numericHistogram = useMemo(() => {
    if (!result || !selectedNumericCol) return null
    const col = result.preview.numeric_columns.find((n) => n.name === selectedNumericCol)
    const counts = asArray<number>(col?.histogram?.counts)
    const edges = asArray<number>(col?.histogram?.bin_edges)
    if (!col || !counts.length || edges.length < 2) return null
    const labels = counts.map((_, i) => `${edges[i].toFixed(2)} ~ ${edges[i + 1].toFixed(2)}`)
    return {
      tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
      grid: { left: 78, right: 34, top: 30, bottom: 108, containLabel: true },
      xAxis: { type: 'category' as const, data: labels, axisLabel: { interval: 0, rotate: 32, hideOverlap: false } },
      yAxis: { type: 'value' as const, name: '样本数', nameGap: 16, axisLabel: { margin: 12 } },
      series: [{ type: 'bar' as const, data: counts, itemStyle: { color: '#16a34a' }, barMaxWidth: 42 }],
    }
  }, [result, selectedNumericCol])

  const scatterOption = useMemo(() => {
    const s = result?.preview.analysis.scatter_plot
    if (!s || !s.points.length) return null
    return {
      tooltip: { trigger: 'item' as const },
      xAxis: { type: 'value' as const, name: cleanLabel(s.x_col) },
      yAxis: { type: 'value' as const, name: cleanLabel(s.y_col) },
      series: [{ type: 'scatter' as const, symbolSize: 8, itemStyle: { color: '#0284c7', opacity: 0.8 }, data: s.points.map((p) => [p.x, p.y]) }],
    }
  }, [result])

  const corrOption = useMemo(() => {
    const c = result?.preview.analysis.corr_heatmap
    if (!c || !c.columns.length || !c.matrix.length) return null
    const data: Array<[number, number, number]> = []
    for (let i = 0; i < c.matrix.length; i += 1) {
      for (let j = 0; j < c.matrix[i].length; j += 1) {
        const v = c.matrix[i][j]
        if (v === null || v === undefined) continue
        data.push([j, i, v])
      }
    }
    return {
      tooltip: { trigger: 'item' as const },
      xAxis: { type: 'category' as const, data: c.columns.map((v) => cleanLabel(v)), axisLabel: { interval: 0, rotate: 32, formatter: (v: string) => shortLabel(v, 14) } },
      yAxis: { type: 'category' as const, data: c.columns.map((v) => shortLabel(v, 14)) },
      visualMap: { min: -1, max: 1, calculable: true, orient: 'horizontal' as const, left: 'center' as const, bottom: 8 },
      series: [{
        type: 'heatmap' as const,
        data,
        label: {
          show: true,
          fontSize: 10,
          formatter: (params: { data: [number, number, number] }) => Number(params.data[2]).toFixed(2),
          color: '#1f2937',
        },
      }],
    }
  }, [result])

  const pcaOption = useMemo(() => {
    const p = result?.preview.analysis.pca_projection
    if (!p || !p.points.length) return null
    const p1 = Number(((p.explained_variance_ratio?.[0] ?? 0) * 100).toFixed(1))
    const p2 = Number(((p.explained_variance_ratio?.[1] ?? 0) * 100).toFixed(1))
    return {
      tooltip: { trigger: 'item' as const },
      xAxis: { type: 'value' as const, name: `PC1 (${p1}%)` },
      yAxis: { type: 'value' as const, name: `PC2 (${p2}%)` },
      series: [{ type: 'scatter' as const, symbolSize: 8, itemStyle: { color: '#7c3aed', opacity: 0.85 }, data: p.points.map((x) => [x.x, x.y]) }],
    }
  }, [result])

  const sampleHeaders = tableRows[0] ? Object.keys(tableRows[0]) : []
  const displayStart = tableTotal ? tableOffset + 1 : 0
  const displayEnd = Math.min(tableOffset + tableRows.length, tableTotal)
  const isZipDataset = Boolean(result?.dataset.filename?.toLowerCase().endsWith('.zip'))

  return (
    <div className="app-shell flex flex-col bg-background lg:flex-row">
      <MLSidebar />
      <MLMobileNav />
      <main className="app-scrollbar flex-1 p-4 md:p-6">
        <div className="mx-auto max-w-7xl space-y-5">
          <section className="hero-panel overflow-hidden rounded-[30px] border border-border p-6 md:p-8">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-border/80 bg-white/80 px-3 py-1 text-xs uppercase tracking-[0.18em] text-muted-foreground">
              <Database className="size-3.5" />
              数据集实时可视化
            </div>
            <h1 className="text-2xl font-semibold tracking-tight md:text-4xl">数据集上传与预览</h1>
            <p className="mt-3 text-sm leading-6 text-muted-foreground md:text-base">
              CSV 可视化分析与 ZIP 图像数据集管理共用同一数据集库，并支持历史回看、删除与批量删除。
            </p>
          </section>

          <Card className="surface-panel rounded-3xl border border-border/80 p-5 md:p-6">
            <form onSubmit={onSubmit} className="grid gap-3 md:grid-cols-[1.2fr_1fr_1fr_auto]">
              <input type="file" accept=".csv,text/csv,.zip,application/zip" onChange={(e) => setFile(e.target.files?.[0] ?? null)} className="rounded-xl border border-border/80 bg-white px-3 py-2 text-sm" />
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="数据集名称（可选）" className="rounded-xl border border-border/80 bg-white px-3 py-2 text-sm" />
              <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="描述（可选）" className="rounded-xl border border-border/80 bg-white px-3 py-2 text-sm" />
              <button type="submit" disabled={uploading} className="inline-flex items-center justify-center gap-2 rounded-xl border border-foreground bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-60">
                <UploadCloud className="size-4" />
                {uploading ? '上传中...' : '上传并可视化'}
              </button>
            </form>
          </Card>

          <Card className="rounded-3xl border border-border/80 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="inline-flex items-center gap-2 text-sm font-medium"><History className="size-4" />历史上传数据集</p>
              <div className="flex items-center gap-2">
                <button type="button" onClick={toggleSelectAllHistory} className="rounded-md border border-border/80 px-3 py-1 text-xs">{allHistorySelected ? '取消全选' : '全选'}</button>
                <button type="button" disabled={selectedHistoryIds.length === 0} onClick={() => void onBatchDelete()} className="rounded-md border border-red-300 px-3 py-1 text-xs text-red-600 disabled:opacity-50">批量删除（{selectedHistoryIds.length}）</button>
                <button type="button" onClick={() => void refreshHistory()} className="rounded-md border border-border/80 px-3 py-1 text-xs">刷新</button>
              </div>
            </div>
            {historyLoading ? <p className="text-sm text-muted-foreground">加载中...</p> : null}
            {!historyLoading && history.length === 0 ? <p className="text-sm text-muted-foreground">暂无历史数据集。</p> : null}
            {history.length > 0 ? (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {history.map((item) => {
                  const checked = selectedHistoryIds.includes(item.id)
                  return (
                    <div key={item.id} className={`rounded-xl border p-3 ${selectedDatasetId === item.id ? 'border-foreground bg-muted/30' : 'border-border/70'}`}>
                      <label className="mb-1 inline-flex items-center gap-2 text-xs text-muted-foreground">
                        <input type="checkbox" checked={checked} onChange={() => toggleHistorySelect(item.id)} />
                        选择
                      </label>
                      <p className="truncate text-sm font-medium" title={item.name}>{item.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{item.created_at} 路 {item.size}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{`样本 ${item.samples.toLocaleString()} · 特征 ${item.features}`}</p>
                      <p className="mt-1 truncate text-xs text-muted-foreground" title={item.description}>{item.description || '无描述'}</p>
                      <div className="mt-2 flex gap-2">
                        <button type="button" onClick={() => void selectDataset(item.id)} className="rounded-md border border-border/80 px-3 py-1 text-xs">查看</button>
                        <button type="button" onClick={() => void onDeleteDataset(item)} className="rounded-md border border-red-300 px-3 py-1 text-xs text-red-600">删除</button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : null}
          </Card>

          {result ? (
            <>
              <div className="grid gap-3 sm:grid-cols-3">
                <Card className="rounded-2xl border border-border/80 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">总行数</p>
                  <p className="mt-2 text-2xl font-semibold">{result.preview.row_count.toLocaleString()}</p>
                </Card>
                <Card className="rounded-2xl border border-border/80 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">参与统计行数</p>
                  <p className="mt-2 text-2xl font-semibold">{result.preview.profiled_rows.toLocaleString()}</p>
                </Card>
                <Card className="rounded-2xl border border-border/80 p-4">
                  <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">字段数量</p>
                  <p className="mt-2 text-2xl font-semibold">{result.preview.columns.length.toLocaleString()}</p>
                </Card>
              </div>

              <Card className="rounded-3xl border border-border/80 p-4">
                <div className="mb-3 flex flex-wrap gap-2">
                  <button type="button" onClick={() => setAnalysisTab('hist')} className={`rounded-full border px-3 py-1.5 text-sm ${analysisTab === 'hist' ? 'border-foreground bg-foreground text-background' : 'border-border/80 bg-white text-muted-foreground'}`}>直方图</button>
                  <button type="button" onClick={() => setAnalysisTab('scatter')} className={`rounded-full border px-3 py-1.5 text-sm ${analysisTab === 'scatter' ? 'border-foreground bg-foreground text-background' : 'border-border/80 bg-white text-muted-foreground'}`}>散点图</button>
                  <button type="button" onClick={() => setAnalysisTab('corr')} className={`rounded-full border px-3 py-1.5 text-sm ${analysisTab === 'corr' ? 'border-foreground bg-foreground text-background' : 'border-border/80 bg-white text-muted-foreground'}`}>相关系数热力图</button>
                  <button type="button" onClick={() => setAnalysisTab('pca')} className={`rounded-full border px-3 py-1.5 text-sm ${analysisTab === 'pca' ? 'border-foreground bg-foreground text-background' : 'border-border/80 bg-white text-muted-foreground'}`}>PCA 降维</button>
                </div>
                {analysisTab === 'hist' ? (numericHistogram ? <ReactECharts option={numericHistogram} notMerge style={{ height: 360 }} /> : <p className="text-sm text-muted-foreground">当前数据不足以生成直方图。</p>) : null}
                {analysisTab === 'scatter' ? (scatterOption ? <ReactECharts option={scatterOption} notMerge style={{ height: 360 }} /> : <p className="text-sm text-muted-foreground">当前数据不足以生成散点图。</p>) : null}
                {analysisTab === 'corr' ? (corrOption ? <ReactECharts option={corrOption} notMerge style={{ height: 460 }} /> : <p className="text-sm text-muted-foreground">当前数据不足以生成热力图。</p>) : null}
                {analysisTab === 'pca' ? (pcaOption ? <ReactECharts option={pcaOption} notMerge style={{ height: 360 }} /> : <p className="text-sm text-muted-foreground">当前数据不足以生成 PCA 图。</p>) : null}
              </Card>

              <Card className="rounded-3xl border border-border/80 p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm font-medium">样例数据</p>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <span>{`总条数 ${tableTotal.toLocaleString()}`}</span>
                    <span>{`当前 ${displayStart.toLocaleString()} - ${displayEnd.toLocaleString()}`}</span>
                  </div>
                </div>
                <div className="mb-3 grid gap-3 rounded-xl border border-border/70 p-3 md:grid-cols-3">
                  <label className="flex flex-col gap-1 text-xs text-muted-foreground">每页条数<div className="flex gap-2"><input value={pageSizeInput} onChange={(e) => setPageSizeInput(e.target.value)} className="w-full rounded-lg border border-border/80 bg-white px-2 py-1 text-sm text-foreground" /><button type="button" onClick={() => void onApplyPageSize()} className="rounded-lg border border-border/80 px-3 py-1 text-sm text-foreground">应用</button></div></label>
                  <label className="flex flex-col gap-1 text-xs text-muted-foreground">跳转页码<div className="flex gap-2"><input value={jumpPageInput} onChange={(e) => setJumpPageInput(e.target.value)} className="w-full rounded-lg border border-border/80 bg-white px-2 py-1 text-sm text-foreground" /><button type="button" onClick={() => void onJumpPage()} className="rounded-lg border border-border/80 px-3 py-1 text-sm text-foreground">跳转</button></div></label>
                  <div className="flex flex-col justify-end gap-2 text-xs text-muted-foreground">
                    <span>{`第 ${currentPage}/${totalPages} 页`}</span>
                    <div className="flex gap-2">
                      <button type="button" disabled={loadingRows || tableOffset <= 0} onClick={() => void loadRows(result.dataset.id, 0)} className="rounded-md border border-border/80 px-2 py-1 disabled:opacity-50">首页</button>
                      <button type="button" disabled={loadingRows || tableOffset <= 0} onClick={() => void loadRows(result.dataset.id, Math.max(0, tableOffset - pageSize))} className="rounded-md border border-border/80 px-2 py-1 disabled:opacity-50">上一页</button>
                      <button type="button" disabled={loadingRows || tableOffset + pageSize >= tableTotal} onClick={() => void loadRows(result.dataset.id, tableOffset + pageSize)} className="rounded-md border border-border/80 px-2 py-1 disabled:opacity-50">下一页</button>
                      <button type="button" disabled={loadingRows || tableOffset + pageSize >= tableTotal} onClick={() => void loadRows(result.dataset.id, (totalPages - 1) * pageSize)} className="rounded-md border border-border/80 px-2 py-1 disabled:opacity-50">末页</button>
                    </div>
                  </div>
                </div>
                {tableRows.length ? (
                  isZipDataset ? (
                    <div className="max-h-[680px] overflow-auto rounded-lg border border-border/60 p-3">
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
                        {tableRows.map((row, idx) => (
                          <div key={`${tableOffset}-${idx}`} className="rounded-xl border border-border/70 bg-white/70 p-2">
                            <div className="mb-2 overflow-hidden rounded-lg border border-border/60 bg-muted/20">
                              {row.path ? (
                                <img
                                  src={`/api/datasets/${result?.dataset.id}/image?path=${encodeURIComponent(String(row.path))}`}
                                  alt={String(row.file_name ?? row.path)}
                                  className="aspect-square w-full object-cover"
                                  loading="lazy"
                                />
                              ) : (
                                <div className="flex aspect-square items-center justify-center text-xs text-muted-foreground">无图片</div>
                              )}
                            </div>
                            <p className="truncate text-sm" title={String(row.label ?? '')}>
                              {row.label || '未标注'}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="max-h-[560px] overflow-auto rounded-lg border border-border/60">
                      <table className="min-w-full text-left text-sm">
                        <thead>
                          <tr className="sticky top-0 z-10 border-b border-border/70 bg-background">
                            <th className="px-2 py-2 font-medium text-muted-foreground">#</th>
                            {sampleHeaders.map((h) => (
                              <th key={h} className="px-2 py-2 font-medium text-muted-foreground">
                                {cleanLabel(h)}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {tableRows.map((row, idx) => (
                            <tr key={`${tableOffset}-${idx}`} className="border-b border-border/40 odd:bg-muted/20">
                              <td className="px-2 py-2 text-muted-foreground">{(tableOffset + idx + 1).toLocaleString()}</td>
                              {sampleHeaders.map((h) => (
                                <td key={`${tableOffset}-${idx}-${h}`} className="max-w-[260px] truncate px-2 py-2" title={String(row[h] ?? '')}>
                                  {row[h] ?? ''}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                ) : <p className="text-sm text-muted-foreground">{loadingRows ? '加载中...' : '暂无样例行。'}</p>}
              </Card>
            </>
          ) : null}
        </div>
      </main>
    </div>
  )
}

