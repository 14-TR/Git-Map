/**
 * Git-Map OpenClaw Plugin
 * Proxies tool calls to the gitmap-skill Python server on port 7400.
 */

const SERVER_URL = "http://localhost:7400";

async function callTool(name: string, args: Record<string, unknown>) {
  const res = await fetch(`${SERVER_URL}/tools/${name}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  const data = await res.json();
  const text = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  return { content: [{ type: "text", text }] };
}

export default function (api: any) {
  api.registerTool(
    {
      name: "gitmap_list",
      description: "List available web maps from ArcGIS Portal/AGOL.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query (e.g. 'title:MyMap')" },
          owner: { type: "string", description: "Filter by owner username" },
          tag: { type: "string", description: "Filter by tag" },
          max_results: { type: "number", description: "Max results (default 100)" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_list", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_status",
      description: "Show working tree status for a GitMap repository.",
      parameters: {
        type: "object",
        properties: {
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_status", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_commit",
      description: "Commit the current map state to the GitMap repository.",
      parameters: {
        type: "object",
        properties: {
          message: { type: "string", description: "Commit message" },
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
          author: { type: "string", description: "Optional author override" },
        },
        required: ["message"],
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_commit", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_branch",
      description: "List, create, or delete branches in a GitMap repository.",
      parameters: {
        type: "object",
        properties: {
          action: { type: "string", enum: ["list", "create", "delete"], description: "Branch action" },
          name: { type: "string", description: "Branch name (for create/delete)" },
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
        required: ["action"],
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_branch", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_diff",
      description: "Show differences between the current index and a branch or commit.",
      parameters: {
        type: "object",
        properties: {
          target: { type: "string", description: "Branch name or commit hash to compare against (default: HEAD)" },
          verbose: { type: "boolean", description: "Show detailed property-level changes" },
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_diff", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_push",
      description: "Push committed map changes to ArcGIS Portal/AGOL.",
      parameters: {
        type: "object",
        properties: {
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_push", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_pull",
      description: "Pull latest map state from ArcGIS Portal/AGOL.",
      parameters: {
        type: "object",
        properties: {
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_pull", params);
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "gitmap_log",
      description: "View commit history for a GitMap repository.",
      parameters: {
        type: "object",
        properties: {
          limit: { type: "number", description: "Number of commits to show (default 10)" },
          branch: { type: "string", description: "Branch to show history for" },
          repo_path: { type: "string", description: "Path to the GitMap repo directory" },
        },
      },
      async execute(_id: string, params: Record<string, unknown>) {
        return callTool("gitmap_log", params);
      },
    },
    { optional: true },
  );
}
