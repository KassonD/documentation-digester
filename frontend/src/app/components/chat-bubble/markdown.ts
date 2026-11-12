import MarkdownIt from 'markdown-it';

// Raw HTML in an answer stays text. Only http(s) links open in a new tab.
const markdown = new MarkdownIt({
  html: false,
  linkify: false,
  typographer: false,
  breaks: false,
});

markdown.renderer.rules['link_open'] = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const href = String(token.attrGet('href') ?? '');
  if (/^https?:\/\//i.test(href)) {
    token.attrSet('target', '_blank');
    token.attrSet('rel', 'noopener noreferrer');
  }
  return self.renderToken(tokens, idx, options);
};

export function renderMarkdown(source: string): string {
  return markdown.render(source);
}
