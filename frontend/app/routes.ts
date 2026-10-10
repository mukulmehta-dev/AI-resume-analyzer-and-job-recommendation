import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("auth", "routes/auth.tsx"),
  route("upload", "routes/upload.tsx"),
  route("resumes", "routes/resumes.tsx"),
  route("analysis/:id", "routes/analysis.tsx"),
  route("history", "routes/history.tsx"),
  route("admin", "routes/admin.tsx"),
  route("help", "routes/help.tsx"),
] satisfies RouteConfig;
