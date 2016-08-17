## Daily Task
### 个别用户无法显示当日数据和任务/ 段时间后，页面刷新无响应
修改数据库获取方式，将全局sql_session调整为局部(一个请求)申请，局部释放
**tips：修改了所有数据库查询，插入操作**

### 设置日志
添加server.log用于记录DEBUG级别信息，添加error.log记录ERROR级别信息
tips:暂未添加使用

### 增加config文件
将配置信息加入config中

### 增加404 403 处理
对于HTTP产生404 403 状态 增加响应页面

### 修改 error.html
将error页面中 user_home的 href 修改令其指向 “/userHome”

### 问题反馈
在type==2级别的用户页面中，没有exportTasks/exportReports的btn。