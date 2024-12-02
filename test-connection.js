const http = require('http');

// 配置参数
const config = {
  host: '你的IP地址',  // 例如: '192.168.1.1'
  port: 你的端口号,    // 例如: 3000
  path: '/',          // 测试的路径
  method: 'GET'
};

// 测试连接函数
function testConnection() {
  const req = http.request(config, (res) => {
    console.log('状态码:', res.statusCode);
    console.log('响应头:', res.headers);

    res.on('data', (chunk) => {
      console.log('响应数据:', chunk.toString());
    });

    res.on('end', () => {
      console.log('请求完成');
    });
  });

  req.on('error', (error) => {
    console.error('请求出错:', error);
  });

  // 设置请求超时时间（毫秒）
  req.setTimeout(5000, () => {
    console.error('请求超时');
    req.destroy();
  });

  req.end();
}

// 执行测试
console.log('开始测试连接...');
testConnection(); 