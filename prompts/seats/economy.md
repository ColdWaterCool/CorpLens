# 席位：经济（公开演示版）

输出经济框架与图表 JSON。禁止编造精确营收。可用调查中的人数与薪资带做粗算。

### 框架·经济
#### 调查与人力成本
人数 / 薪资区间 / 均值 / 月人力粗算（推断）
#### 成本与收入（展开写）
人力 / 原料 / 租金 / 获客 / 收入方式
#### PEC政经文
政策关注点（待核验）/ 市场结构 / 地方好感 / 综合含义
#### 经济理论要点
2～3 条，结合本案
#### 价值抓手与边际
#### 图表数据
```json
{
  "optimization": [
    {"item": "预约沟通耗时", "ratio": 30},
    {"item": "复购留存", "ratio": 25},
    {"item": "排班峰值", "ratio": 20},
    {"item": "平台抽成", "ratio": 15},
    {"item": "其他", "ratio": 10}
  ],
  "marginal": [
    {"item": "老客预约", "benefit": 40, "effort": 25},
    {"item": "服务SOP", "benefit": 35, "effort": 30},
    {"item": "内容获客", "benefit": 25, "effort": 35},
    {"item": "全城投放", "benefit": 15, "effort": 75}
  ],
  "combo": [
    {"lever": "流程线上化", "efficiency": 40, "revenue": 20, "risk_down": 25},
    {"lever": "会员沉淀", "efficiency": 25, "revenue": 35, "risk_down": 20},
    {"lever": "近端深耕", "efficiency": 30, "revenue": 30, "risk_down": 30}
  ]
}
```
