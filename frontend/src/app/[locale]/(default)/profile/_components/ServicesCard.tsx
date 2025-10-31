'use client'

import styles from '../_assets/page.module.scss'

interface Service {
  id: string
  name: string
  icon: string
  status: 'active' | 'inactive' | 'pending'
  plan: string
  nextBilling?: string
}

interface ServicesCardProps {
  services: Service[]
}

export function ServicesCard({ services }: ServicesCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#22D49F'
      case 'inactive':
        return '#64748b'
      case 'pending':
        return '#FAA61A'
      default:
        return '#64748b'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Active'
      case 'inactive':
        return 'Inactive'
      case 'pending':
        return 'Pending'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className={styles.profileStatsCard}>
      <div className={styles.servicesHeader}>
        <h3 className={styles.profileSubtitle}>Services</h3>
        <span className={styles.servicesCount}>{services.length} subscribed</span>
      </div>

      <div className={styles.servicesList}>
        {services.map((service) => (
          <div key={service.id} className={styles.serviceItem}>
            <div className={styles.serviceIcon}>
              <span className={styles.serviceEmoji}>{service.icon}</span>
            </div>
            <div className={styles.serviceInfo}>
              <div className={styles.serviceHeader}>
                <h4 className={styles.serviceName}>{service.name}</h4>
                <span
                  className={styles.serviceStatus}
                  style={{ color: getStatusColor(service.status) }}>
                  {getStatusText(service.status)}
                </span>
              </div>
              <div className={styles.serviceDetails}>
                <span className={styles.servicePlan}>{service.plan}</span>
                {service.nextBilling && (
                  <span className={styles.serviceBilling}>Next: {service.nextBilling}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
