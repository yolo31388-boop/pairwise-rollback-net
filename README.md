# pairwise-rollback-net

联机对战的确定性回滚现在有严重问题：Boss 的 selector 每次都重新选中已经 running 的子节点，导致同一个攻击被重复触发；parallel 节点在所有子节点成功后还在 tick；blackboard 的 key 在回滚后没有恢复；同一输入在重放时被应用两次；float 精度在 60/120fps 下不一致；客户端预测和服务器确认的 tick 对不上；RNG 在回滚后继续前进，导致随机弹道偏移。net/rollback.py 是核心，tests/test_rollback.py 15个红。要修的是：snapshot/restore 覆盖完整状态；hash 与字段顺序无关；advance 固定 tick 并衰减冷却；rollback 从快照重放确认输入且不重复应用；compare_states 检测位置/血量 desync；RNG 在回滚后恢复到同一序列。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。
