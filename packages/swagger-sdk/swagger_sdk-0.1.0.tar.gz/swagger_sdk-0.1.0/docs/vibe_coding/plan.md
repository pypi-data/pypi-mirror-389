# 开发计划 - TDD 方式

## 阶段一：核心功能（MVP）

### 1. 枚举类定义
- [x] 测试：ParamIn 枚举类
- [x] 测试：HttpMethod 枚举类
- [x] 测试：SchemaType 枚举类
- [x] 测试：Format 枚举类
- [x] 测试：ContentType 枚举类
- [x] 实现：所有枚举类 ✅

### 2. 基础类定义
- [x] 测试：Parameter 类
- [x] 测试：Field 类
- [x] 测试：Schema 类
- [x] 测试：RequestBody 类
- [x] 测试：ResponseContent 类
- [x] 测试：Response 类
- [x] 实现：所有基础类 ✅

### 3. SwaggerBuilder 基础类
- [x] 测试：SwaggerBuilder 初始化
- [x] 测试：register_api 方法
- [x] 实现：SwaggerBuilder 类 ✅

### 4. 装饰器定义
- [x] 测试：@swagger_api 装饰器基本功能
- [x] 测试：@swagger_controller 装饰器基本功能
- [x] 实现：装饰器 ✅

### 5. JSON 生成
- [x] 测试：生成基本的 OpenAPI 3.0 JSON
- [x] 测试：包含路径和操作的 JSON
- [x] 测试：包含参数和响应的 JSON
- [x] 实现：generate_json 方法 ✅

## 阶段二：增强功能

### 6. 扫描功能
- [x] 测试：扫描模块中的装饰器函数
- [x] 测试：扫描类中的装饰器方法
- [x] 实现：scan 方法 ✅

### 7. 类型注解解析
- [x] 测试：解析基本类型（int, str, bool）
- [x] 测试：解析 Optional 类型
- [x] 测试：解析 List 和 Dict 类型
- [x] 实现：类型注解解析器 ✅

### 8. 文档字符串解析
- [x] 测试：解析 Google 风格 docstring
- [x] 测试：解析参数描述
- [x] 实现：docstring 解析器 ✅

### 9. YAML 生成
- [x] 测试：生成 YAML 格式
- [x] 实现：YAML 序列化器 ✅

## 阶段三：功能整合与增强

### 10. 扫描功能增强（整合解析器）
- [x] 测试：扫描时自动提取函数签名参数
- [x] 测试：扫描时自动提取 docstring 描述
- [x] 测试：扫描时自动生成 Parameter 列表
- [x] 测试：扫描时自动生成 Response schema
- [x] 实现：Scanner 集成 TypeParser 和 DocstringParser ✅

### 11. dataclass 模型支持
- [x] 测试：解析 dataclass 模型
- [x] 测试：生成 dataclass 的 schema
- [x] 测试：支持嵌套 dataclass
- [x] 实现：dataclass 解析器 ✅

### 12. Components/Schemas 支持
- [x] 测试：定义和重用 schema 组件
- [x] 测试：生成 Components 部分
- [x] 实现：Components 管理器 ✅

### 13. HTML 生成
- [x] 测试：生成基本的 HTML 文档
- [x] 测试：集成 Swagger UI
- [x] 实现：HTML 模板引擎 ✅

### 14. 文档验证
- [x] 测试：验证 OpenAPI 3.0 语法
- [x] 测试：验证语义正确性
- [x] 实现：文档验证器 ✅

### 15. 文档预览
- [x] 测试：启动预览服务器
- [x] 测试：实时更新预览
- [x] 实现：预览功能 ✅

## 阶段四：辅助功能

### 16. 批量注册接口
- [x] 测试：批量注册多个接口
- [x] 实现：register_apis 方法 ✅

### 17. 接口更新功能
- [x] 测试：更新已注册的接口
- [x] 实现：update_api 方法 ✅

### 18. 配置管理
- [x] 测试：从配置文件加载配置
- [x] 测试：从环境变量加载配置
- [x] 实现：配置管理器 ✅

### 19. 日志和调试
- [x] 测试：日志输出功能
- [x] 测试：调试模式
- [x] 实现：日志系统 ✅

### 20. 错误处理增强
- [x] 测试：完善的错误信息
- [x] 实现：错误处理和异常类 ✅

## 阶段五：测试和优化

### 21. 集成测试
- [x] 测试：完整流程集成测试
- [x] 测试：多场景测试 ✅

### 22. 性能优化
- [x] 测试：扫描性能测试
- [x] 测试：生成性能测试
- [x] 优化：扫描算法优化 ✅

### 23. 兼容性测试
- [x] 测试：Python 3.8-3.12 兼容性
- [x] 测试：跨平台兼容性 ✅

### 24. 文档完善
- [x] 用户文档：快速开始指南
- [x] API 参考文档
- [x] 使用示例和最佳实践 ✅

## 阶段六：增强功能（可选）

### 25. NumPy 风格 docstring 解析
- [ ] 测试：解析 NumPy 风格 docstring
- [ ] 实现：NumPy 风格解析器

### 26. YAML 配置文件支持
- [ ] 测试：从 YAML 配置文件加载配置
- [ ] 实现：YAML 配置文件解析（使用自实现的 YAML 解析器）

### 27. 测试支持功能
- [ ] 测试：生成测试用例模板
- [ ] 测试：接口测试验证
- [ ] 测试：生成测试报告
- [ ] 实现：测试支持模块

### 28. 安全定义（Security）支持
- [x] 测试：定义安全方案（API Key、OAuth2、Bearer 等）
- [x] 测试：在接口中应用安全定义
- [x] 测试：生成 Security 部分的 OpenAPI 文档
- [x] 实现：Security 定义和生成 ✅

### 29. 插件系统
- [ ] 测试：自定义装饰器支持
- [ ] 测试：自定义解析器支持
- [ ] 测试：插件注册和加载机制
- [ ] 实现：插件系统框架