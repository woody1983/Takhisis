# Issue #10 配件需求工单系统 - 技术方案分析

## 需求理解

### 核心功能
1. **工单创建**: 客服提交配件补发需求
2. **数据字段**: SKU、配件代码、数量
3. **入口位置**: 配件系统首页上方

### 用户场景
- 客服收到客户反馈配件缺失/损坏
- 需要在配件管理系统中创建补发工单
- 仓库人员根据工单进行配件补发

---

## 方案分析

### 方案一：简单工单表（推荐）

**数据库设计：**
```sql
CREATE TABLE work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL,                    -- 产品SKU
    accessory_code TEXT NOT NULL,         -- 配件代码
    quantity INTEGER NOT NULL,            -- 数量
    status TEXT DEFAULT 'pending',        -- 状态: pending/completed/cancelled
    customer_service_name TEXT,           -- 客服姓名
    remark TEXT,                          -- 备注
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP                -- 完成时间
);
```

**功能模块：**
1. ✅ 工单列表页（首页上方入口）
2. ✅ 创建工单表单（SKU、配件代码、数量）
3. ✅ 工单状态管理（待处理/已完成/已取消）
4. ✅ 工单筛选和搜索

**开发难度：** ⭐⭐ 简单
**预计时间：** 2-3 小时
**优点：**
- 实现简单，快速上线
- 满足基本需求
- 易于维护

---

### 方案二：完整工单工作流

**数据库设计：**
```sql
CREATE TABLE work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,    -- 工单编号 WO-20240219-001
    sku TEXT NOT NULL,
    accessory_code TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',        -- pending/processing/completed/cancelled
    priority TEXT DEFAULT 'normal',       -- low/normal/high/urgent
    customer_service_id INTEGER,          -- 客服ID（关联用户表）
    warehouse_id INTEGER,                 -- 处理仓库人员ID
    remark TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE work_order_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER,
    action TEXT,                          -- create/update/complete/cancel
    operator TEXT,
    details TEXT,
    created_at TIMESTAMP
);
```

**功能模块：**
1. ✅ 工单列表（带分页、筛选）
2. ✅ 创建工单（自动编号）
3. ✅ 工单详情页
4. ✅ 状态流转（待处理→处理中→已完成）
5. ✅ 操作日志
6. ✅ 优先级标记
7. ✅ 统计报表（每日工单量、处理时效）

**开发难度：** ⭐⭐⭐⭐ 中等偏复杂
**预计时间：** 6-8 小时
**优点：**
- 功能完整，可扩展性强
- 有操作审计
- 支持多客服协作

---

### 方案三：集成库存检查

在方案二基础上增加：

**额外功能：**
1. 提交时自动检查库存
2. 库存不足时标记预警
3. 库存扣减联动
4. 补发后自动更新配件位置

**开发难度：** ⭐⭐⭐⭐⭐ 复杂
**预计时间：** 10-12 小时
**风险：**
- 需要修改现有库存逻辑
- 并发处理复杂

---

## 技术实现建议

### 推荐方案：方案一（简单工单表）

**理由：**
1. 当前需求明确且简单，不需要过度设计
2. 快速上线验证需求
3. 后续可根据实际使用情况迭代升级

### 实现步骤：

1. **数据库迁移** (15分钟)
   - 创建 work_orders 表

2. **后端API** (30分钟)
   - GET /work_orders - 工单列表
   - POST /work_orders - 创建工单
   - PUT /work_orders/<id> - 更新状态
   - GET /work_orders/<id> - 工单详情

3. **前端页面** (60分钟)
   - 首页添加工单入口按钮
   - 工单列表页
   - 创建工单表单
   - 工单详情/操作页

4. **测试** (30分钟)
   - 创建工单测试
   - 状态流转测试

### UI 设计建议：

```
┌─────────────────────────────────────┐
│  Accessory Management          [工单系统] │  ← 首页添加入口
├─────────────────────────────────────┤
│                                     │
│  [添加工单]  [待处理(5)] [已完成(12)] │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ SKU      配件代码  数量  状态 │   │
│  │ ABC123   CODE-01    2   待处理│   │
│  │ XYZ789   CODE-02    1   已完成│   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

## 问题澄清

在开发前需要确认：

1. **配件代码**是否需要预先定义？还是自由文本输入？
2. **客服身份**需要登录验证吗？还是直接输入姓名？
3. **工单状态**需要哪些？（待处理、已完成、已取消？）
4. **是否需要通知功能**？（如工单创建后通知仓库）
5. **数据保留策略**？工单完成后保留多久？

---

## 总结

| 方案 | 难度 | 时间 | 推荐度 |
|------|------|------|--------|
| 方案一：简单工单 | ⭐⭐ | 2-3h | ⭐⭐⭐⭐⭐ |
| 方案二：完整工作流 | ⭐⭐⭐⭐ | 6-8h | ⭐⭐⭐ |
| 方案三：集成库存 | ⭐⭐⭐⭐⭐ | 10-12h | ⭐⭐ |

**建议采用方案一快速上线，后续根据使用反馈迭代。**
