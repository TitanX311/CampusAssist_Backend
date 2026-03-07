"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/store/AuthContext";
import { Card, CardHeader, CardContent, Button, Input, Badge, Alert, TableActions, TableActionsCompact, TableHeaderActions } from "@/components";
import { AdminLayout } from "@/components/AdminLayout";

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (user?.type === "SUPER_ADMIN") {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-secondary dark:bg-dark-bg-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin inline-block w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mb-4" />
          <p className="text-text-secondary dark:text-dark-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-primary-600 via-primary-500 to-accent-500 shadow-elevation-3">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 right-0 w-96 h-96 rounded-full blur-3xl bg-white" />
            <div className="absolute bottom-0 left-1/4 w-64 h-64 rounded-full blur-2xl bg-secondary-400" />
          </div>
          <div className="relative p-8 sm:p-12">
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-3">Campus Assist</h1>
            <p className="text-white/90 text-lg max-w-2xl leading-relaxed">
              Powerful admin dashboard for managing colleges, communities, users, and content. Built for scalability and performance.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Button variant="outline" className="bg-white text-primary-600 border-white hover:bg-white/90">
                Documentation
              </Button>
              <Button variant="ghost" className="text-white border border-white/30 hover:bg-white/10">
                Support Center
              </Button>
            </div>
          </div>
        </div>

        {/* Status Alerts */}
        <div className="space-y-3">
          <h2 className="text-lg font-bold text-text-primary dark:text-dark-text-primary">System Status</h2>
          <div className="grid grid-cols-1 gap-3">
            <Alert type="success" title="All Systems Operational" dismissible>
              Our services are running smoothly with 99.9% uptime.
            </Alert>
            <Alert type="info" title="Pro Tip" dismissible>
              Use keyboard shortcuts (⌘/Ctrl + K) to quickly navigate to any section.
            </Alert>
          </div>
        </div>

        {/* Key Metrics */}
        <div>
          <h2 className="text-lg font-bold text-text-primary dark:text-dark-text-primary mb-4">Key Metrics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { 
                label: 'Total Users',
                value: '12,543',
                trend: '+12.5%',
                trendUp: true,
                icon: '👥',
                bgColor: 'from-blue-500/10 to-blue-600/10'
              },
              { 
                label: 'Colleges',
                value: '48',
                trend: '+2 new',
                trendUp: true,
                icon: '🏫',
                bgColor: 'from-emerald-500/10 to-emerald-600/10'
              },
              { 
                label: 'Communities',
                value: '324',
                trend: '+8.3%',
                trendUp: true,
                icon: '👫',
                bgColor: 'from-purple-500/10 to-purple-600/10'
              },
              { 
                label: 'Posts',
                value: '5,842',
                trend: '+22.1%',
                trendUp: true,
                icon: '📝',
                bgColor: 'from-orange-500/10 to-orange-600/10'
              },
            ].map((stat) => (
              <Card key={stat.label} hoverable elevation="md" className="overflow-hidden">
                <div className={`absolute inset-0 bg-gradient-to-br ${stat.bgColor} opacity-40`} />
                <CardContent className="p-6 relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className="text-3xl">{stat.icon}</div>
                    <div className="flex items-center gap-1 text-xs font-semibold text-success-DEFAULT bg-success-light px-2 py-1 rounded-full">
                      <span>↑</span>
                      <span>{stat.trend}</span>
                    </div>
                  </div>
                  <div className="text-text-tertiary dark:text-dark-text-tertiary text-sm font-medium mb-1">
                    {stat.label}
                  </div>
                  <div className="text-3xl font-bold text-text-primary dark:text-dark-text-primary">
                    {stat.value}
                  </div>
                  <div className="mt-4 h-1.5 bg-bg-tertiary dark:bg-dark-bg-secondary rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full" style={{ width: '75%' }} />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Component Library Showcase */}
        <div>
          <h2 className="text-lg font-bold text-text-primary dark:text-dark-text-primary mb-4">Component Library</h2>
          <div className="space-y-6">
            {/* Buttons Section */}
            <Card>
              <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔘</span>
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Button Variants</h3>
                </div>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">All available button styles and states</p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-3">Default States</label>
                    <div className="flex flex-wrap gap-3">
                      <Button variant="primary">Primary</Button>
                      <Button variant="secondary">Secondary</Button>
                      <Button variant="outline">Outline</Button>
                      <Button variant="danger">Danger</Button>
                      <Button variant="ghost">Ghost</Button>
                    </div>
                  </div>
                  <div className="border-t border-border-primary dark:border-dark-border-primary pt-4">
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-3">Sizes</label>
                    <div className="flex flex-wrap items-center gap-3">
                      <Button size="sm" variant="primary">Small</Button>
                      <Button size="md" variant="primary">Medium</Button>
                      <Button size="lg" variant="primary">Large</Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Form Elements Section */}
            <Card>
              <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📝</span>
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Form Elements</h3>
                </div>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">Input fields, validation, and helper text</p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input
                    label="Full Name"
                    placeholder="Enter your full name"
                    helperText="Please use your legal name"
                  />
                  <Input
                    label="Email Address"
                    type="email"
                    placeholder="Enter your email"
                  />
                  <Input
                    label="Success State"
                    defaultValue="Successfully validated"
                    disabled
                  />
                  <Input
                    label="Error State"
                    defaultValue="Invalid input"
                    error="This field is required"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Badges & Status Section */}
            <Card>
              <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🏷️</span>
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Badges & Status Indicators</h3>
                </div>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">Status badges for categorization and filtering</p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-3">Semantic Variants</label>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="primary">Primary</Badge>
                      <Badge variant="secondary">Active</Badge>
                      <Badge variant="success">Success</Badge>
                      <Badge variant="warning">Warning</Badge>
                      <Badge variant="error">Error</Badge>
                      <Badge variant="info">Information</Badge>
                      <Badge variant="neutral">Neutral</Badge>
                    </div>
                  </div>
                  <div className="border-t border-border-primary dark:border-dark-border-primary pt-4">
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-3">Sizes</label>
                    <div className="flex flex-wrap gap-2">
                      <Badge size="sm">Small Badge</Badge>
                      <Badge size="md">Medium Badge</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Color Palette Section */}
            <Card>
              <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎨</span>
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Color Palette</h3>
                </div>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">Professional color system for all UI elements</p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                  {[
                    { name: 'Primary', bg: 'bg-gradient-to-br from-primary-400 to-primary-600', hex: '#4f46e5' },
                    { name: 'Secondary', bg: 'bg-gradient-to-br from-secondary-400 to-secondary-600', hex: '#14b8a6' },
                    { name: 'Accent', bg: 'bg-gradient-to-br from-accent-400 to-accent-600', hex: '#f59e0b' },
                    { name: 'Success', bg: 'bg-gradient-to-br from-emerald-400 to-emerald-600', hex: '#10b981' },
                    { name: 'Warning', bg: 'bg-gradient-to-br from-amber-400 to-amber-600', hex: '#f59e0b' },
                    { name: 'Error', bg: 'bg-gradient-to-br from-red-400 to-red-600', hex: '#ef4444' },
                    { name: 'Info', bg: 'bg-gradient-to-br from-cyan-400 to-cyan-600', hex: '#0ea5e9' },
                    { name: 'Neutral', bg: 'bg-gradient-to-br from-neutral-400 to-neutral-600', hex: '#64748b' },
                  ].map((color) => (
                    <div key={color.name}>
                      <div className={`${color.bg} w-full h-24 rounded-lg mb-2 shadow-elevation-1 hover:shadow-elevation-2 transition-shadow`} />
                      <p className="text-sm font-semibold text-text-primary dark:text-dark-text-primary">{color.name}</p>
                      <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary font-mono">{color.hex}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Table Actions Section */}
            <Card>
              <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
                <div className="flex items-center gap-2">
                  <span className="text-lg">📋</span>
                  <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Table Actions</h3>
                </div>
                <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">Action buttons for data tables and rows</p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-6">
                  {/* Icon-Based Actions */}
                  <div>
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-4">Icon-Based Actions (Compact)</label>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="border-b border-border-primary dark:border-dark-border-primary">
                          <tr>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">User Name</th>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Email</th>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Status</th>
                            <th className="text-right px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-primary dark:divide-dark-border-primary">
                          {[
                            { name: 'John Doe', email: 'john@example.com', status: 'active' },
                            { name: 'Jane Smith', email: 'jane@example.com', status: 'pending' },
                            { name: 'Alex Johnson', email: 'alex@example.com', status: 'active' },
                          ].map((row) => (
                            <tr key={row.email} className="hover:bg-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors">
                              <td className="px-4 py-3 text-text-primary dark:text-dark-text-primary font-medium">{row.name}</td>
                              <td className="px-4 py-3 text-text-secondary dark:text-dark-text-secondary">{row.email}</td>
                              <td className="px-4 py-3">
                                <Badge variant={row.status === 'active' ? 'success' : 'warning'}>
                                  {row.status}
                                </Badge>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <TableActions
                                  onView={() => console.log('View:', row.name)}
                                  onEdit={() => console.log('Edit:', row.name)}
                                  onDelete={() => console.log('Delete:', row.name)}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Text-Based Compact Actions */}
                  <div className="border-t border-border-primary dark:border-dark-border-primary pt-6">
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-4">Text-Based Actions (Compact)</label>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="border-b border-border-primary dark:border-dark-border-primary">
                          <tr>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">College Name</th>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Location</th>
                            <th className="text-left px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Students</th>
                            <th className="text-right px-4 py-3 font-semibold text-text-primary dark:text-dark-text-primary">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-border-primary dark:divide-dark-border-primary">
                          {[
                            { name: 'Tech Institute', location: 'New York', students: '2,450' },
                            { name: 'Business Academy', location: 'Los Angeles', students: '1,890' },
                            { name: 'Engineering Hub', location: 'San Francisco', students: '3,200' },
                          ].map((row) => (
                            <tr key={row.name} className="hover:bg-bg-secondary dark:hover:bg-dark-bg-secondary transition-colors">
                              <td className="px-4 py-3 text-text-primary dark:text-dark-text-primary font-medium">{row.name}</td>
                              <td className="px-4 py-3 text-text-secondary dark:text-dark-text-secondary">{row.location}</td>
                              <td className="px-4 py-3 text-text-secondary dark:text-dark-text-secondary">{row.students}</td>
                              <td className="px-4 py-3 text-right">
                                <TableActionsCompact
                                  onView={() => console.log('View:', row.name)}
                                  onEdit={() => console.log('Edit:', row.name)}
                                  onDelete={() => console.log('Delete:', row.name)}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Header Actions */}
                  <div className="border-t border-border-primary dark:border-dark-border-primary pt-6">
                    <label className="text-xs font-semibold text-text-secondary dark:text-dark-text-secondary uppercase tracking-wide block mb-4">Table Header Actions</label>
                    <div className="p-4 bg-bg-secondary dark:bg-dark-bg-secondary rounded-lg">
                      <TableHeaderActions
                        onAddNew={() => console.log('Add new')}
                        onRefresh={() => console.log('Refresh')}
                        onExport={() => console.log('Export')}
                        onImport={() => console.log('Import')}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Quick Actions */}
        <Card>
          <CardHeader className="border-b border-border-primary dark:border-dark-border-primary">
            <div className="flex items-center gap-2">
              <span className="text-lg">⚡</span>
              <h3 className="text-base font-semibold text-text-primary dark:text-dark-text-primary">Quick Actions</h3>
            </div>
            <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary mt-1">Common tasks and operations</p>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                { label: '+ Create College', variant: 'primary' as const },
                { label: '+ Create Community', variant: 'secondary' as const },
                { label: '📊 Export Report', variant: 'outline' as const },
                { label: '📋 View Logs', variant: 'ghost' as const },
              ].map((action) => (
                <Button
                  key={action.label}
                  fullWidth
                  variant={action.variant}
                  className="justify-center"
                >
                  {action.label}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Footer Info */}
        <div className="border-t border-border-primary dark:border-dark-border-primary pt-8 pb-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <div>
              <h4 className="text-sm font-bold text-text-primary dark:text-dark-text-primary mb-2">Documentation</h4>
              <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">Learn how to use every feature and component of the admin panel.</p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text-primary dark:text-dark-text-primary mb-2">API Reference</h4>
              <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">Complete API documentation for all microservices.</p>
            </div>
            <div>
              <h4 className="text-sm font-bold text-text-primary dark:text-dark-text-primary mb-2">Support</h4>
              <p className="text-xs text-text-tertiary dark:text-dark-text-tertiary">Contact our support team for help and troubleshooting.</p>
            </div>
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
