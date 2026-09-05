// Local QA only. Node 24 built-in WebSocket; Chrome DevTools on loopback.
import { writeFile } from 'node:fs/promises';
const endpoint = 'http://127.0.0.1:19222';
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const target = targets.find(t => t.type === 'page');
if (!target) throw new Error('No browser page');
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
let sequence = 0;
const pending = new Map();
const exceptions = [];
socket.onmessage = ({ data }) => {
  const message = JSON.parse(data);
  if (message.method === 'Runtime.exceptionThrown') exceptions.push(message.params);
  const request = pending.get(message.id);
  if (request) {
    clearTimeout(request.timer);
    pending.delete(message.id);
    if (message.error) request.reject(new Error(JSON.stringify(message.error)));
    else request.resolve(message.result);
  }
};
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timeout: ${method}`)); }, 15000);
    pending.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
try {
  await send('Runtime.enable');
  await send('Page.enable');
  if (process.argv[2] === 'inspect') {
    await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false });
    await send('Page.navigate', { url: 'http://127.0.0.1:5173/proof' });
    await pause(2500);
  } else if (process.argv[2] === 'eval') {
    console.log(JSON.stringify(await evaluate(process.argv[3]), null, 2));
    await pause(400);
  }
  console.log(JSON.stringify(await evaluate(`({url:location.href,text:document.body.innerText,controls:[...document.querySelectorAll('button,input,select,textarea,a')].map(e=>({tag:e.tagName,text:e.innerText,label:e.getAttribute('aria-label'),name:e.name,id:e.id,type:e.type,disabled:e.disabled})),width:innerWidth,scrollWidth:document.documentElement.scrollWidth})`), null, 2));
  if (process.argv[2] === 'screenshot') {
    const image = await send('Page.captureScreenshot', { format: 'png' });
    await writeFile(new URL('./browser-desktop.png', import.meta.url), Buffer.from(image.data, 'base64'));
  }
  console.log(JSON.stringify({ exceptions }));
} finally {
  socket.close();
}