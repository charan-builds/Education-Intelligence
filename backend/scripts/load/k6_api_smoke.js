import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    dashboard_load: {
      executor: "ramping-arrival-rate",
      startRate: 20,
      timeUnit: "1s",
      preAllocatedVUs: 50,
      maxVUs: 500,
      stages: [
        { target: 50, duration: "1m" },
        { target: 200, duration: "2m" },
        { target: 500, duration: "2m" },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500", "p(99)<1000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, { "health ok": (r) => r.status === 200 });
  sleep(1);
}
