interface WellnessSectionProps {
  icon: string;
  title: string;
  description: string;
  bgColor?: string;
  iconColor?: string;
  children?: React.ReactNode;
}

export default function WellnessSection({
  icon,
  title,
  description,
  bgColor = 'bg-emerald-50',
  iconColor = 'text-[#006036]',
  children,
}: WellnessSectionProps) {
  return (
    <div className="bg-white rounded-lg p-8 diffusion-shadow hover:-translate-y-0.5 transition-all duration-300">
      <div className={`w-14 h-14 ${bgColor} rounded-2xl flex items-center justify-center mb-6`}>
        <span className={`material-symbols-outlined text-2xl ${iconColor}`} style={{ fontVariationSettings: "'FILL' 1" }}>
          {icon}
        </span>
      </div>
      <h3 className="text-lg font-bold text-[#191c1b] font-headline mb-3">{title}</h3>
      <p className="text-sm text-[#3f4941] leading-relaxed">{description}</p>
      {children && <div className="mt-6">{children}</div>}
    </div>
  );
}
