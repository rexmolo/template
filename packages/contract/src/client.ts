import createClient, { type ClientOptions } from "openapi-fetch";

import type { paths } from "./types.js";

export function createApiClient(options: ClientOptions = {}) {
  return createClient<paths>(options);
}

export type ApiClient = ReturnType<typeof createApiClient>;
