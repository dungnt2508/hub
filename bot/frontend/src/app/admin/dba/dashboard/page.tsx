'use client';

import React, { useState } from 'react';
import DBADashboard from '@/components/DBADashboard';
import AdminLayout from '@/components/AdminLayout';

export default function DBADashboardPage() {
  const [selectedConnection, setSelectedConnection] = useState<string | undefined>();

  return (
    <AdminLayout>
      <DBADashboard connectionId={selectedConnection} />
    </AdminLayout>
  );
}
