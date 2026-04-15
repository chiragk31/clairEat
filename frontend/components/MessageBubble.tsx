import { Message } from '@/types/chat';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-md signature-gradient text-white p-5 rounded-3xl rounded-tr-none diffusion-shadow">
          <p className="text-sm font-medium leading-relaxed">{message.content}</p>
          <p className="text-[10px] text-white/70 mt-2 font-medium text-right">{message.time}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4">
      {/* AI avatar */}
      <div className="w-8 h-8 shrink-0 rounded-full signature-gradient flex items-center justify-center">
        <span
          className="material-symbols-outlined text-white text-sm"
          style={{ fontVariationSettings: "'FILL' 1" }}
        >
          psychology
        </span>
      </div>

      {/* AI bubble */}
      <div className="bg-[#f3f4f1] p-5 rounded-3xl rounded-tl-none max-w-2xl border border-[#bec9be]/10">
        <p className="text-sm text-[#191c1b] leading-relaxed">{message.content}</p>
        {message.loading && (
          <div className="flex gap-1 mt-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#006036] animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-[#006036] animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-[#006036] animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        )}
        {!message.loading && (
          <p className="text-[10px] text-[#6f7a70] mt-2 font-medium">{message.time}</p>
        )}
      </div>
    </div>
  );
}
