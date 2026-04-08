def validate_classification_sequence(data):
    """
    验证标本分类字段的传递顺序

    修正规则：
    1. 必须从1-1开始
    2. 每一级的分类必须按顺序填写，不能跳过
    3. 如果某个分类为空，后面的同级分类也必须为空
    4. 允许跳过整个层级（比如只有1级，或者只有1、2级）

    例如：
    ✅ 有效：1-1, 1-2, 1-3, 2-1, 3-1（这是允许的！）
    ✅ 有效：1-1, 1-2, 2-1
    ✅ 有效：1-1, 2-1, 2-2
    ❌ 无效：2-1（没有1-1）
    ❌ 无效：1-1, 1-3（跳过了1-2）
    ❌ 无效：1-1, 2-2（跳过了2-1）
    """

    # 定义分类的层级和顺序
    classification_levels = [
        ['标本分类1-1', '标本分类1-2', '标本分类1-3', '标本分类1-4'],
        ['标本分类2-1', '标本分类2-2', '标本分类2-3', '标本分类2-4'],
        ['标本分类3-1', '标本分类3-2', '标本分类3-3', '标本分类3-4']
    ]

    # 1. 检查是否从第一级开始
    if '标本分类1-1' not in data or not data.get('标本分类1-1'):
        return False, "必须从'标本分类1-1'开始填写"

    # 2. 检查每一级内部的连续性
    for level_fields in classification_levels:
        # 检查当前层级的第一个字段
        first_field = level_fields[0]
        has_first_field = first_field in data and data.get(first_field)

        if not has_first_field:
            # 如果当前级第一个字段为空，检查后面的字段是否也都为空
            for field in level_fields[1:]:
                if field in data and data.get(field):
                    return False, f"不能跳过'{first_field}'直接填写'{field}'"
            continue  # 当前级完全为空，继续下一级

        # 检查当前级内部的连续性
        found_empty = False
        for i, field in enumerate(level_fields):
            has_value = field in data and bool(data.get(field))

            if not has_value:
                found_empty = True
                # 检查后面的字段是否都为空
                for j in range(i + 1, len(level_fields)):
                    next_field = level_fields[j]
                    if next_field in data and data.get(next_field):
                        return False, f"'{field}'为空时，后面的'{next_field}'不能有值"
            elif found_empty:
                # 如果已经找到空值，但后面又有值
                return False, f"不能跳过空值填写'{field}'"

    return True, "验证通过"