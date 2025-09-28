// 이 파일은 createApp으로 만든 Express 서버를 실제로 띄우는 진입점입니다.
// 설정된 포트 번호로 서버를 실행하고 콘솔에 접속 주소를 보여줍니다.

import { createApp } from './app.js';
import { config } from './config.js';

const app = createApp();

app.listen(config.port, () => {
  // eslint-disable-next-line no-console
  console.log(`API listening on http://localhost:${config.port}`);
});
