import { observable, action, computed } from 'mobx-miniprogram'

export const store = observable({
  // ===== Dashboard 数据 =====
  dashboardData: null,
  dashboardLoading: false,
  dashboardError: '',

  // ===== 竞品数据 =====
  competitors: [],
  competitorLoading: false,

  // ===== 舆情数据 =====
  sentiments: [],
  sentimentLoading: false,

  // ===== 预警数据 =====
  alerts: [],
  alertCount: 0,

  // ===== 报告数据 =====
  reportContent: '',
  reportGenerating: false,

  // ===== 计算属性 =====
  get totalGMV() {
    if (!this.dashboardData) return '0'
    return (this.dashboardData.total_gmv / 10000).toFixed(0)
  },

  get gmvGrowth() {
    if (!this.dashboardData || !this.dashboardData.gmv_trend) return '0'
    const arr = this.dashboardData.gmv_trend
    if (arr.length < 2) return '0'
    const latest = arr[arr.length - 1].value
    const prev = arr[arr.length - 2].value
    return ((latest - prev) / (prev || 1) * 100).toFixed(1)
  },

  // ===== Actions =====
  setDashboardData: action(function (data) {
    this.dashboardData = data
    this.dashboardLoading = false
  }),

  setDashboardLoading: action(function (loading) {
    this.dashboardLoading = loading
  }),

  setDashboardError: action(function (err) {
    this.dashboardError = err
    this.dashboardLoading = false
  }),

  setCompetitors: action(function (data) {
    this.competitors = data
    this.competitorLoading = false
  }),

  setCompetitorLoading: action(function (loading) {
    this.competitorLoading = loading
  }),

  setSentiments: action(function (data) {
    this.sentiments = data
    this.sentimentLoading = false
  }),

  setAlerts: action(function (data) {
    this.alerts = data
    this.alertCount = data.length
  }),

  setReportContent: action(function (content) {
    this.reportContent = content
    this.reportGenerating = false
  }),

  setReportGenerating: action(function (generating) {
    this.reportGenerating = generating
  }),
})
