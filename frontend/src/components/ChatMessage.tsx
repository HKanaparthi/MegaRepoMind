import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { FileCode, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import type { Message } from '../types'

interface Props {
  message: Message
}

export default function ChatMessage({ message }: Props) {
  const [showCitations, setShowCitations] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'order-1' : ''}`}>
        {!isUser && (
          <div className="text-xs text-brand-400 font-medium mb-1 ml-1">MegaRepoMind</div>
        )}
        <div className={`rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-brand-600 text-white rounded-br-sm'
            : 'bg-gray-800 text-gray-100 rounded-bl-sm'
        }`}>
          {isUser ? (
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-dark text-sm">
              <ReactMarkdown
                components={{
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '')
                    const inline = !match
                    return inline ? (
                      <code className={className} {...props}>{children}</code>
                    ) : (
                      <SyntaxHighlighter
                        style={vscDarkPlus}
                        language={match[1]}
                        PreTag="div"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 ml-1">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
            >
              <FileCode className="w-3 h-3" />
              {message.citations.length} source{message.citations.length > 1 ? 's' : ''}
              {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
            {showCitations && (
              <div className="mt-2 space-y-2">
                {message.citations.map((c, i) => (
                  <div key={i} className="bg-gray-900 border border-gray-700 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-mono text-brand-300">{c.file_path}</span>
                      <span className="text-xs text-gray-500">L{c.start_line}–{c.end_line}</span>
                    </div>
                    <pre className="text-xs text-gray-400 font-mono overflow-x-auto whitespace-pre-wrap">
                      {c.snippet}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
