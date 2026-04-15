'use client';

import { usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import TopBar from '@/components/TopBar';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  // Pages that should not display the sidebar and topbar
  const noLayoutRoutes = ['/onboarding'];
  const hideLayout = noLayoutRoutes.includes(pathname);

  if (hideLayout) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-surface flex">
      {/* Fixed Sidebar */}
      <Sidebar />
      
      {/* Main Content Area */}
      <div className="ml-0 md:ml-64 flex flex-col flex-1 min-h-screen w-full">
        <TopBar />
        <main className="flex-1 w-full bg-surface pb-12">
          {children}
        </main>
      </div>
    </div>
  );
}
