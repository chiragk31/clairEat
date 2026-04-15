interface DashboardCardProps {
  title: string;
  description: string;
  icon: string;
  iconColor?: string;
  iconBg?: string;
  borderColor?: string;
}

export default function DashboardCard({
  title,
  description,
  icon,
  iconColor = 'text-primary',
  iconBg = 'bg-primary/10',
  borderColor = 'border-primary',
}: DashboardCardProps) {
  return (
    <div className={`bg-white p-6 rounded-lg diffusion-shadow border-l-4 ${borderColor} hover:-translate-y-0.5 transition-all duration-300`}>
      <div className="flex items-center gap-4 mb-3">
        <div className={`w-10 h-10 rounded-full ${iconBg} flex items-center justify-center ${iconColor}`}>
          <span className="material-symbols-outlined">{icon}</span>
        </div>
        <h4 className="font-headline font-bold text-[#191c1b]">{title}</h4>
      </div>
      <p className="text-sm text-[#3f4941] leading-relaxed">{description}</p>
    </div>
  );
}
