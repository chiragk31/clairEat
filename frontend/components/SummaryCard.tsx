interface SummaryCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: string;
  iconColor?: string;
  iconBg?: string;
  accentColor?: string;
  trend?: string;
  trendUp?: boolean;
}

export default function SummaryCard({
  label,
  value,
  subValue,
  icon,
  iconColor = 'text-primary',
  iconBg = 'bg-emerald-50',
  trend,
  trendUp,
}: SummaryCardProps) {
  return (
    <div className="bg-white rounded-lg p-6 diffusion-shadow border border-stone-100 hover:-translate-y-0.5 transition-all duration-300 group">
      {icon && (
        <div className={`w-11 h-11 ${iconBg} rounded-xl flex items-center justify-center mb-4 group-hover:scale-105 transition-transform`}>
          <span className={`material-symbols-outlined ${iconColor}`} style={{ fontVariationSettings: "'FILL' 1" }}>
            {icon}
          </span>
        </div>
      )}
      <p className="text-xs font-bold uppercase tracking-widest text-stone-400 mb-1">{label}</p>
      <p className="text-2xl font-bold text-[#191c1b] font-headline">{value}</p>
      {subValue && <p className="text-xs text-stone-500 mt-1">{subValue}</p>}
      {trend && (
        <p className={`text-xs font-bold mt-2 flex items-center gap-1 ${trendUp ? 'text-emerald-600' : 'text-red-500'}`}>
          <span className="material-symbols-outlined text-sm">{trendUp ? 'trending_up' : 'trending_down'}</span>
          {trend}
        </p>
      )}
    </div>
  );
}
