import { ConvexHttpClient } from "convex/browser";
import { api } from "../../convex/_generated/api";

const CONVEX_URL = import.meta.env.VITE_CONVEX_URL || import.meta.env.PUBLIC_CONVEX_URL;

export const convex = new ConvexHttpClient(CONVEX_URL);
export { api };
