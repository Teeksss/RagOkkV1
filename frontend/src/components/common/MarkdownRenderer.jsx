import React from 'react';
import PropTypes from 'prop-types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

/**
 * Component for rendering Markdown content with syntax highlighting
 * 
 * @param {Object} props Component props
 * @param {string} props.content Markdown content to render
 * @param {boolean} props.allowHtml Whether to allow HTML in markdown
 * @returns {JSX.Element} Rendered markdown
 */
const MarkdownRenderer = ({ content, allowHtml = false }) => {
  if (!content) return null;

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[allowHtml ? rehypeRaw : rehypeSanitize]}
      className="markdown-content"
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              style={atomDark}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
        // Custom link renderer to ensure links open in new tab
        a: ({ node, children, href, ...props }) => (
          <a 
            href={href} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="text-blue-600 hover:text-blue-800 underline"
            {...props}
          >
            {children}
          </a>
        ),
        // Custom image renderer with proper styling
        img: ({ node, ...props }) => (
          <img
            className="max-w-full h-auto rounded my-2"
            loading="lazy"
            {...props}
          />
        ),
        // Custom table styling
        table: ({ node, children, ...props }) => (
          <div className="overflow-x-auto my-4">
            <table className="min-w-full divide-y divide-gray-300 border border-gray-300" {...props}>
              {children}
            </table>
          </div>
        ),
        thead: ({ node, ...props }) => (
          <thead className="bg-gray-50" {...props} />
        ),
        th: ({ node, children, ...props }) => (
          <th
            className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b"
            {...props}
          >
            {children}
          </th>
        ),
        td: ({ node, children, ...props }) => (
          <td
            className="px-3 py-2 whitespace-nowrap text-sm text-gray-500 border-b border-gray-200"
            {...props}
          >
            {children}
          </td>
        ),
        // Custom blockquote styling
        blockquote: ({ node, children, ...props }) => (
          <blockquote
            className="border-l-4 border-gray-300 pl-4 py-0.5 my-2 text-gray-700"
            {...props}
          >
            {children}
          </blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

MarkdownRenderer.propTypes = {
  content: PropTypes.string.isRequired,
  allowHtml: PropTypes.bool
};

export default MarkdownRenderer;