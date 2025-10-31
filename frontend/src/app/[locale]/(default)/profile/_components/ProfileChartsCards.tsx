'use client'

import { CapsHistory, RankHistory } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileChartsCardsProps {
  rankHistory: RankHistory[]
  capsHistory: CapsHistory[]
}

export function ProfileChartsCards({
  rankHistory: _rankHistory,
  capsHistory: _capsHistory,
}: ProfileChartsCardsProps) {
  // Enhanced chart with smooth curves and professional styling
  const renderRankChart = () => (
    <svg width="100%" height="200" viewBox="0 0 320 200" className={styles.chartSvg}>
      {/* Grid lines */}
      <defs>
        <linearGradient id="rankGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FAA61A" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#FAA61A" stopOpacity="0.05" />
        </linearGradient>
      </defs>

      {/* Horizontal grid lines */}
      {[40, 80, 120, 160].map((y, i) => (
        <line
          key={i}
          x1="20"
          y1={y}
          x2="300"
          y2={y}
          stroke="#2d3748"
          strokeWidth="1"
          opacity="0.3"
        />
      ))}

      {/* Area fill */}
      <path
        d="M 20,170 Q 50,120 80,130 Q 110,90 140,85 Q 170,95 200,65 Q 230,50 260,45 L 260,180 L 20,180 Z"
        fill="url(#rankGradient)"
      />

      {/* Main line with smooth curve */}
      <path
        d="M 20,170 Q 50,120 80,130 Q 110,90 140,85 Q 170,95 200,65 Q 230,50 260,45"
        fill="none"
        stroke="#FAA61A"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {[
        { x: 20, y: 170 },
        { x: 80, y: 130 },
        { x: 140, y: 85 },
        { x: 200, y: 65 },
        { x: 260, y: 45 },
      ].map((point, i) => (
        <circle
          key={i}
          cx={point.x}
          cy={point.y}
          r="4"
          fill="#FAA61A"
          stroke="#1e293b"
          strokeWidth="2"
        />
      ))}
    </svg>
  )

  const renderCapsChart = () => (
    <svg width="100%" height="200" viewBox="0 0 320 200" className={styles.chartSvg}>
      {/* Grid and gradient definitions */}
      <defs>
        <linearGradient id="capsGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#22D49F" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#22D49F" stopOpacity="0.05" />
        </linearGradient>
      </defs>

      {/* Horizontal grid lines */}
      {[40, 80, 120, 160].map((y, i) => (
        <line
          key={i}
          x1="20"
          y1={y}
          x2="300"
          y2={y}
          stroke="#2d3748"
          strokeWidth="1"
          opacity="0.3"
        />
      ))}

      {/* Area fill */}
      <path
        d="M 20,150 Q 50,135 80,125 Q 110,110 140,105 Q 170,85 200,70 Q 230,55 260,50 L 260,180 L 20,180 Z"
        fill="url(#capsGradient)"
      />

      {/* Main line with smooth curve */}
      <path
        d="M 20,150 Q 50,135 80,125 Q 110,110 140,105 Q 170,85 200,70 Q 230,55 260,50"
        fill="none"
        stroke="#22D49F"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Data points */}
      {[
        { x: 20, y: 150 },
        { x: 80, y: 125 },
        { x: 140, y: 105 },
        { x: 200, y: 70 },
        { x: 260, y: 50 },
      ].map((point, i) => (
        <circle
          key={i}
          cx={point.x}
          cy={point.y}
          r="4"
          fill="#22D49F"
          stroke="#1e293b"
          strokeWidth="2"
        />
      ))}
    </svg>
  )

  return (
    <>
      {/* Card 1 (Left): Rank Dynamics */}
      <div className={styles.profileChartCard}>
        <div className={styles.chartHeader}>
          <h4 className={styles.profileSubtitle}>Rank Dynamics</h4>
          <span className={styles.chartValue}>Rank #12</span>
        </div>
        <div className={styles.profileLineChart}>{renderRankChart()}</div>
        <div className={styles.profileChartFooter}>
          <span className={styles.chartMetric}>Best Rank: #5</span>
          <span className={styles.chartTrend}>↗ +7 this month</span>
        </div>
      </div>

      {/* Card 2 (Right): CAPs Dynamics */}
      <div className={styles.profileChartCard}>
        <div className={styles.chartHeader}>
          <h4 className={styles.profileSubtitle}>CAPs Dynamics</h4>
          <span className={styles.chartValue}>34,540 CAPS</span>
        </div>
        <div className={styles.profileLineChart}>{renderCapsChart()}</div>
        <div className={styles.profileChartFooter}>
          <span className={styles.chartMetric}>Total Earned: 34,540</span>
          <span className={styles.chartTrend}>↗ +250 this week</span>
        </div>
      </div>
    </>
  )
}
