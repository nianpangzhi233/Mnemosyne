# WriteGate 自定义步骤示例 — 开发计划

## 目标

为 `WriteGate.register_step(name, fn)` 提供真实业务场景的示例步骤，展示系统的可扩展性，并写入文档。

---

## 原子任务

### T1: 编写重复内容检测步骤

- 新建 `v8/src/v8_memory/gate_steps.py`
- 实现 `check_duplicate_content(candidate_id, store)` → 检查是否有 content 相同的已验证记忆
- 返回 `{passed: bool, reason: string}`
- 如果有重复，返回 `passed=false, reason="duplicate of memory {id}"`
- 如果无重复，返回 `passed=true`
- **验收**：用已有的 candidate 和 memory 数据测试，重复的被拦住，不重复的通过

### T2: 编写风险关键词过滤步骤

- 在 `gate_steps.py` 中实现 `check_risk_keywords(candidate_id, store)` → 检查 candidate content 是否包含高风险关键词（密码、密钥、token 等敏感信息）
- 高风险词表：`["password", "secret", "api_key", "token", "private_key", "credential", "密码", "密钥"]`
- 返回 `{passed: bool, reason: string}`
- 匹配到任一关键词 → `passed=false, reason="contains sensitive keyword: {keyword}"`
- **验收**：含 "password" 的 candidate 被拦住，正常内容通过

### T3: 编写注册入口

- 在 `gate_steps.py` 中实现 `register_default_steps(write_gate)` 函数
- 一行注册所有示例步骤：`write_gate.register_step("duplicate_check", check_duplicate_content)` 和 `write_gate.register_step("risk_keywords", check_risk_keywords)`
- **验收**：调用后 `write_gate.custom_steps` 包含两个步骤

### T4: 编写测试

- 新建 `tests/test_gate_steps.py`
- 测试用例：
  - `test_duplicate_pass` — 无重复内容，通过
  - `test_duplicate_block` — 有重复内容，被拦
  - `test_risk_keywords_pass` — 正常内容，通过
  - `test_risk_keywords_block` — 含敏感词，被拦
  - `test_register_default_steps` — 注册后步骤存在
- **验收**：5 个测试全通过

### T5: 文档更新

- `v8/README.md` — 加 gate_steps 使用示例段落
- `README.md` — Design Decision Log 加"为什么用 Python callable 不用 YAML"
- `CHANGELOG.md` — 加 gate_steps 条目
- **验收**：文档中有完整的使用示例代码

---

## 不在范围内

- 不做自动注册（用户需要手动调用 `register_default_steps`）
- 不做 LLM 驱动的验证步骤（保持 zero-dependency）

## 依赖

- T3 依赖 T1 + T2
- T4 依赖 T1 + T2 + T3
- T5 依赖 T4

## 预估工作量

| 任务 | 时间 |
|------|------|
| T1: 重复内容检测 | 15 分钟 |
| T2: 风险关键词过滤 | 15 分钟 |
| T3: 注册入口 | 5 分钟 |
| T4: 测试 | 20 分钟 |
| T5: 文档 | 15 分钟 |
| **合计** | **约 1 小时** |

## 关键文件

- `v8/src/v8_memory/gate_steps.py` — 新建，示例步骤
- `tests/test_gate_steps.py` — 新建，测试
- `v8/src/v8_memory/gates.py` — 已有，`register_step` API
- `v8/README.md` — 更新，加使用示例
- `README.md` — 更新，加设计决策
- `CHANGELOG.md` — 更新
