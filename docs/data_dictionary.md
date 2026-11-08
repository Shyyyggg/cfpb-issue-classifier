# CFPB 投诉数据字典

数据来源：CFPB Consumer Complaint Database（公开数据，许可：公共领域 / 开放数据）。
观测单位：一条消费者投诉；全量约 16,545,376 条记录，16 个字段。

| # | 字段名 | 类型 | 含义 | 示例 | 缺失处理 |
|---|--------|------|------|------|----------|
| 1 | `date_received` | 日期 | 投诉被 CFPB 接收的日期（ISO8601） | 2024-01-25T19:56:56.000Z | 缺失/非法日期整条拒绝 |
| 2 | `product` | 分类 | 产品大类（已按历史 schema 归一化） | Credit reporting or other personal consumer reports | 空值记为 UNKNOWN |
| 3 | `sub_product` | 分类 | 产品子类 | Credit reporting | 空值记为 UNKNOWN |
| 4 | `issue` | 标签 | 问题类型（本项目预测目标，181 类） | Incorrect information on your report | 空值记为 UNKNOWN |
| 5 | `sub_issue` | 分类 | 问题子类 | Account status incorrect | 空值记为 UNKNOWN |
| 6 | `narrative` | 文本 | 消费者自述（自由文本，平均 1020 字符） | They keep calling about a debt I do not owe. | 空串表示未提供 |
| 7 | `company_public_response` | 文本 | 公司对 CFPB 的公开回应 | Company has responded to the consumer... | 空值记为 UNKNOWN |
| 8 | `company` | 分类 | 被投诉公司名 | Experian Information Solutions Inc. | 空值记为 UNKNOWN，去除首尾引号 |
| 9 | `state` | 分类 | 消费者所在州（大写两位缩写） | TN | 空值记为 UNKNOWN，统一转大写 |
| 10 | `zip_code` | 分类 | 消费者邮编（5 位） | 38141 | 空值记为 UNKNOWN |
| 11 | `tags` | 分类 | 标签（如 Servicemember） | Older American | 空值记为 UNKNOWN |
| 12 | `submitted_via` | 分类 | 提交渠道 | Web | 空值记为 UNKNOWN |
| 13 | `date_sent_to_company` | 日期 | 投诉转交公司的日期 | 2024-01-25T19:56:59.000Z | 缺失不拒绝 |
| 14 | `company_response` | 分类 | 公司给消费者的处理结果 | Closed with non-monetary relief | 空值记为 UNKNOWN |
| 15 | `timely_response` | 布尔 | 公司是否及时响应（Yes/No） | Yes | 空值记为 UNKNOWN |
| 16 | `complaint_id` | 标识 | 投诉唯一编号 | 8223945 | 空值记为 UNKNOWN |

> 注：`issue` 是本项目的预测目标（多类分类标签），其余字段为可用输入特征。