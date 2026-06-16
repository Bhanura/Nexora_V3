/**
 * Simple Markdown-style formatter for chat messages
 * Converts common markdown patterns to HTML
 */
export default function MarkdownMessage({ content }) {
  const formatMessage = (text) => {
    // Split by newlines to preserve structure
    const lines = text.split('\n');
    const formatted = [];
    let inList = false;

    lines.forEach((line, index) => {
      // Bold text: **text** or __text__
      line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      line = line.replace(/__(.+?)__/g, '<strong>$1</strong>');
      
      // Italic text: *text* or _text_
      line = line.replace(/\*(.+?)\*/g, '<em>$1</em>');
      line = line.replace(/_(.+?)_/g, '<em>$1</em>');
      
      // Code: `code`
      line = line.replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
      
      // Bullet points: * item or - item
      if (line.trim().match(/^[\*\-]\s+/)) {
        if (!inList) {
          formatted.push('<ul class="list-disc list-inside space-y-1 my-2">');
          inList = true;
        }
        const content = line.trim().replace(/^[\*\-]\s+/, '');
        formatted.push(`<li class="ml-2">${content}</li>`);
      } else {
        if (inList) {
          formatted.push('</ul>');
          inList = false;
        }
        
        // Numbered lists: 1. item
        if (line.trim().match(/^\d+\.\s+/)) {
          const content = line.trim().replace(/^\d+\.\s+/, '');
          formatted.push(`<div class="ml-4 my-1">• ${content}</div>`);
        } else if (line.trim()) {
          formatted.push(`<p class="my-1">${line}</p>`);
        } else {
          formatted.push('<br/>');
        }
      }
    });
    
    // Close any open list
    if (inList) {
      formatted.push('</ul>');
    }
    
    return formatted.join('');
  };

  return (
    <div 
      className="prose prose-sm max-w-none"
      dangerouslySetInnerHTML={{ __html: formatMessage(content) }}
    />
  );
}
