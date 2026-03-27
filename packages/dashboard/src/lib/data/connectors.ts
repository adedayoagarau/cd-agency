export type ConnectorStatus = "connected" | "available" | "coming-soon";

export interface Connector {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: ConnectorStatus;
  lastSync?: string;
  entries?: number;
  contentTypes?: number;
}

export const connectors: Connector[] = [
  { id: "contentful", name: "Contentful", description: "Headless CMS for digital-first content", icon: "contentful", status: "connected", lastSync: "2 min ago", entries: 1247, contentTypes: 8 },
  { id: "figma", name: "Figma", description: "Collaborative design and prototyping tool", icon: "figma", status: "connected", lastSync: "15 min ago", entries: 342, contentTypes: 3 },
  { id: "notion", name: "Notion", description: "All-in-one workspace for docs and wikis", icon: "notion", status: "connected", lastSync: "1 hour ago", entries: 89, contentTypes: 5 },
  { id: "sanity", name: "Sanity", description: "Real-time structured content platform", icon: "sanity", status: "available" },
  { id: "strapi", name: "Strapi", description: "Open-source headless CMS", icon: "strapi", status: "available" },
  { id: "wordpress", name: "WordPress", description: "The world's most popular CMS", icon: "wordpress", status: "available" },
  { id: "storyblok", name: "Storyblok", description: "Visual headless CMS for content teams", icon: "storyblok", status: "available" },
  { id: "airtable", name: "Airtable", description: "Spreadsheet-database hybrid for teams", icon: "airtable", status: "available" },
  { id: "google-docs", name: "Google Docs", description: "Collaborative document editing", icon: "google-docs", status: "available" },
  { id: "markdown", name: "Markdown/MDX", description: "Import from local markdown files", icon: "markdown", status: "available" },
  { id: "slack", name: "Slack", description: "Team messaging and collaboration", icon: "slack", status: "coming-soon" },
  { id: "github", name: "GitHub", description: "Code hosting and collaboration platform", icon: "github", status: "coming-soon" },
  { id: "linear", name: "Linear", description: "Issue tracking and project management", icon: "linear", status: "coming-soon" },
  { id: "webflow", name: "Webflow", description: "Visual website builder and CMS", icon: "webflow", status: "coming-soon" },
  { id: "datocms", name: "DatoCMS", description: "API-first headless CMS", icon: "datocms", status: "coming-soon" },
];
