import { apiGet } from "./client";
import type { RegistrySnapshot } from "../types/registry";

export async function fetchRegistry(): Promise<RegistrySnapshot> {
  return apiGet<RegistrySnapshot>("/api/registry");
}
