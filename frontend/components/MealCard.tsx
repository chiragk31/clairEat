interface MealCardProps {
  name: string;
  calories: number;
  prep: string;
  imageEmoji?: string;
  isAiPick?: boolean;
  bgColor?: string;
}

export default function MealCard({
  name,
  calories,
  prep,
  imageEmoji = '🍽️',
  isAiPick = false,
  bgColor = 'bg-emerald-50',
}: MealCardProps) {
  return (
    <div
      className={`bg-white rounded-lg p-3 cursor-pointer group hover:bg-[#edeeeb] transition-all duration-200 diffusion-shadow ${
        isAiPick ? 'ring-2 ring-[#006036]/20' : ''
      }`}
    >
      {/* Meal image placeholder */}
      <div
        className={`w-full h-20 ${bgColor} rounded-md mb-3 flex items-center justify-center text-3xl group-hover:scale-105 transition-transform overflow-hidden relative`}
      >
        <span>{imageEmoji}</span>
        {isAiPick && (
          <div className="absolute top-1 right-1 bg-[#006036] rounded-full p-0.5">
            <span className="material-symbols-outlined text-white text-[10px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              auto_awesome
            </span>
          </div>
        )}
      </div>

      {/* Meal info */}
      <h4 className={`text-xs font-bold leading-tight mb-2 ${isAiPick ? 'text-[#006036]' : 'text-[#191c1b]'}`}>
        {isAiPick ? `AI Pick: ${name}` : name}
      </h4>

      <div className="flex flex-wrap gap-1.5">
        <span
          className={`text-[9px] font-bold px-2 py-0.5 rounded ${
            isAiPick ? 'bg-[#006036]/10 text-[#006036]' : 'bg-[#edeeeb] text-[#6f7a70]'
          }`}
        >
          {calories} kcal
        </span>
        <span
          className={`text-[9px] font-bold px-2 py-0.5 rounded ${
            isAiPick ? 'bg-[#006036]/10 text-[#006036]' : 'bg-[#edeeeb] text-[#6f7a70]'
          }`}
        >
          {prep}
        </span>
      </div>
    </div>
  );
}
