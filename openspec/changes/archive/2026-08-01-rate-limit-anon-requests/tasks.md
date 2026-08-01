## 1. Implement Anonymous Throttle Class

- [x] 1.1 Create `src/sa_api_v2/throttling.py`
- [x] 1.2 Implement `AnonymousIPThrottle` inheriting from `rest_framework.throttling.SimpleRateThrottle`
- [x] 1.3 Implement `allow_request` in `AnonymousIPThrottle` to bypass if `request.user.is_authenticated` or if `request.client` exists
- [x] 1.4 Write tests in `src/sa_api_v2/tests/test_throttling.py` to ensure rate limit only applies to fully anonymous requests

## 2. Configure DRF Settings

- [x] 2.1 Update `REST_FRAMEWORK` dictionary in `src/project/settings.py` to add `DEFAULT_THROTTLE_CLASSES` containing the new `AnonymousIPThrottle`
- [x] 2.2 Configure `DEFAULT_THROTTLE_RATES` with `anon_ip` scoped to the value from the environment variable `ANON_THROTTLE_RATE` (default `20/min`)
- [x] 2.3 Add `NUM_PROXIES` to `REST_FRAMEWORK` sourced from the `NUM_PROXIES` environment variable (defaulting to `None`)

## 3. Verify System Behavior

- [x] 3.1 Run tests to verify the global API configuration correctly applies the throttle to anonymous requests and allows authenticated ones
