/**
 * GlucoTwin Synthetic Mock Data Service
 * Strictly simulated physiological data and patient archetypes.
 * Complies with docs/API_INTEGRATION.md schemas.
 */

export const MOCK_PATIENTS = [
  {
    id: 'GT-9042',
    name: 'Sarah Jenkins',
    age: 34,
    gender: 'Female',
    archetype: 'Type 1 Diabetes (Brittle / High Variability)',
    bmi: 23.4,
    current_glucose: 142,
    trend: 'rising', // 'rising' | 'falling' | 'stable'
    risk_level: 'moderate', // 'low' | 'moderate' | 'high'
    last_synced: '2026-10-10T14:30:00Z',
    demographics: {
      height_cm: 168,
      weight_kg: 66.0,
      diagnosis_year: 2018,
      primary_clinic: 'Metro Endocrinology Associates',
      attending_physician: 'Dr. A. Verma, MD'
    },
    basal_profile: {
      basal_rate_units_per_hour: 0.85,
      insulin_sensitivity_factor: 45,
      carb_insulin_ratio: 12,
      target_range_mgdl: [70, 180]
    },
    lab_history: [
      { date: '2025-06-12', hba1c: 7.6, fasting_glucose: 144 },
      { date: '2025-10-15', hba1c: 7.4, fasting_glucose: 138 },
      { date: '2026-02-10', hba1c: 7.1, fasting_glucose: 126 },
      { date: '2026-06-18', hba1c: 6.9, fasting_glucose: 118 },
      { date: '2026-10-02', hba1c: 6.8, fasting_glucose: 114 }
    ],
    active_medications: [
      { name: 'Insulin Glargine (Basal)', dosage: '20 Units', frequency: 'Nightly at 22:00', adherence_pct: 98 },
      { name: 'Insulin Aspart (Rapid)', dosage: '1 Unit / 12g Carbs', frequency: 'Pre-meal bolus', adherence_pct: 92 },
      { name: 'Continuous Glucose Sensor', dosage: 'Abbott FreeStyle Libre 3', frequency: 'Continuous (5-min)', adherence_pct: 99 }
    ],
    encounters: [
      { date: '2026-09-14', type: 'Routine Endocrinology Follow-up', clinician: 'Dr. A. Verma', notes: 'Reduced nocturnal basal by 0.05 U/hr to curb 04:00 dips. TIR steady at 78%.' },
      { date: '2026-06-20', type: 'Comprehensive Metabolic Panel', clinician: 'Lab Services', notes: 'eGFR > 90 mL/min, Microalbumin negative. HbA1c improved to 6.9%.' },
      { date: '2026-03-12', type: 'Diabetes Educator Consultation', clinician: 'R. Davis, CDCES', notes: 'Reviewed carb-counting accuracy for midday meals. Patient motivated.' }
    ]
  },
  {
    id: 'GT-8105',
    name: 'Ramesh Sharma',
    age: 52,
    gender: 'Male',
    archetype: 'Type 2 Diabetes (Postprandial Spikes)',
    bmi: 28.1,
    current_glucose: 118,
    trend: 'stable',
    risk_level: 'low',
    last_synced: '2026-10-10T14:30:00Z',
    demographics: {
      height_cm: 174,
      weight_kg: 85.0,
      diagnosis_year: 2021,
      primary_clinic: 'City Health Center',
      attending_physician: 'Dr. K. Patel, MD'
    },
    basal_profile: {
      basal_rate_units_per_hour: 0.50,
      insulin_sensitivity_factor: 55,
      carb_insulin_ratio: 15,
      target_range_mgdl: [70, 180]
    },
    lab_history: [
      { date: '2025-08-01', hba1c: 8.2, fasting_glucose: 162 },
      { date: '2025-12-14', hba1c: 7.7, fasting_glucose: 148 },
      { date: '2026-04-20', hba1c: 7.3, fasting_glucose: 132 },
      { date: '2026-09-10', hba1c: 7.0, fasting_glucose: 122 }
    ],
    active_medications: [
      { name: 'Metformin ER', dosage: '1000 mg', frequency: 'Twice daily with meals', adherence_pct: 95 },
      { name: 'Empagliflozin (Jardiance)', dosage: '10 mg', frequency: 'Once daily morning', adherence_pct: 90 }
    ],
    encounters: [
      { date: '2026-09-15', type: 'Endocrine Quarterly Review', clinician: 'Dr. K. Patel', notes: 'Significant glycemic stability achieved with SGLT2i addition.' }
    ]
  },
  {
    id: 'GT-7721',
    name: 'David Chen',
    age: 41,
    gender: 'Male',
    archetype: 'Type 1 Diabetes (Active Lifestyle / Exercise Sensitive)',
    bmi: 24.2,
    current_glucose: 88,
    trend: 'falling',
    risk_level: 'high',
    last_synced: '2026-10-10T14:30:00Z',
    demographics: {
      height_cm: 178,
      weight_kg: 76.5,
      diagnosis_year: 2015,
      primary_clinic: 'University Metabolic Institute',
      attending_physician: 'Dr. E. Gomez, MD'
    },
    basal_profile: {
      basal_rate_units_per_hour: 0.90,
      insulin_sensitivity_factor: 40,
      carb_insulin_ratio: 10,
      target_range_mgdl: [70, 180]
    },
    lab_history: [
      { date: '2025-11-05', hba1c: 6.9, fasting_glucose: 110 },
      { date: '2026-03-14', hba1c: 6.7, fasting_glucose: 105 },
      { date: '2026-07-22', hba1c: 6.5, fasting_glucose: 98 }
    ],
    active_medications: [
      { name: 'Insulin Degludec (Tresiba)', dosage: '22 Units', frequency: 'Once daily morning', adherence_pct: 100 },
      { name: 'Insulin Lispro (Humalog)', dosage: '1 Unit / 10g Carbs', frequency: 'Pre-meal bolus', adherence_pct: 96 }
    ],
    encounters: [
      { date: '2026-08-04', type: 'Sports Endocrinology Consult', clinician: 'Dr. E. Gomez', notes: 'High propensity for late-onset exercise-induced hypoglycemia.' }
    ]
  }
];

/**
 * Generates synthetic continuous telemetry points (CGM + HR + HRV)
 */
export function generateSyntheticTelemetry(patientId = 'GT-9042', hours = 4) {
  const points = [];
  const totalIntervals = (hours * 60) / 5; // 5-minute intervals
  const baseTime = new Date('2026-10-10T14:30:00Z').getTime();

  for (let i = totalIntervals; i >= 0; i--) {
    const timestamp = new Date(baseTime - i * 5 * 60 * 1000);
    const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    
    // Smooth synthetic glycemic curve with meal bump
    const t = (totalIntervals - i) / totalIntervals;
    let glucose = 118 + Math.sin(t * Math.PI * 2) * 22;
    
    // Add realistic meal effect ~1.5 hours ago
    if (i <= 20 && i >= 4) {
      glucose += Math.sin(((20 - i) / 16) * Math.PI) * 28;
    }

    glucose = Math.round(glucose);
    const hr = Math.round(72 + (glucose - 120) * 0.15 + (Math.sin(i) * 4));
    const hrv = Math.round(52 - (glucose - 120) * 0.2 + (Math.cos(i) * 5));

    let event = null;
    if (i === 18) {
      event = { type: 'meal', label: 'Lunch: 52g Carbs', icon: 'meal' };
    } else if (i === 16) {
      event = { type: 'bolus', label: 'Bolus: 4.2 U Rapid', icon: 'insulin' };
    }

    points.push({
      timestamp: timestamp.toISOString(),
      timeStr,
      actualGlucose: glucose,
      predictedGlucose: null,
      ciLower: null,
      ciUpper: null,
      heartRate: hr,
      hrvRmssd: Math.max(20, hrv),
      event
    });
  }

  return points;
}

/**
 * Generates forward-looking 2-hour prediction with confidence cone
 */
export function generateSyntheticPredictions(patientId = 'GT-9042') {
  const baseTime = new Date('2026-10-10T14:30:00Z').getTime();
  const currentGlucose = 142;

  // 15, 30, 45, 60, 75, 90, 105, 120 minutes ahead
  const steps = [0, 15, 30, 45, 60, 75, 90, 105, 120];
  const forecastPoints = steps.map((min) => {
    const time = new Date(baseTime + min * 60 * 1000);
    const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    
    // Spike modeling
    let pred = currentGlucose;
    if (min > 0) {
      pred = currentGlucose + Math.sin((min / 60) * Math.PI * 0.5) * 56;
      if (min > 60) {
        pred -= (min - 60) * 0.8;
      }
    }
    pred = Math.round(pred);

    // Uncertainty expands with time
    const uncertainty = Math.round(min * 0.22);
    const ciLower = Math.max(50, pred - uncertainty);
    const ciUpper = pred + uncertainty;

    return {
      timestamp: time.toISOString(),
      timeStr,
      actualGlucose: min === 0 ? currentGlucose : null,
      predictedGlucose: pred,
      ciLower,
      ciUpper,
      uncertaintyRange: [ciLower, ciUpper]
    };
  });

  return {
    patient_id: patientId,
    forecast_generated_at: '2026-10-10T14:30:00Z',
    horizon_minutes: 120,
    risk_assessment: {
      spike_probability_pct: 58.0,
      risk_tier: 'moderate', // 'low' (0-30%), 'moderate' (31-60%), 'high' (61-100%)
      projected_peak_mgdl: 198,
      time_to_peak_minutes: 60,
      hypo_risk_pct: 6.0
    },
    forecast_points: forecastPoints
  };
}

/**
 * Synthetic SHAP feature attribution values for Explainable AI
 */
export function getMockXaiFeatures(patientId = 'GT-9042') {
  return [
    {
      id: 'f1',
      name: 'Active Carbohydrate Digestion (Lunch)',
      impact_mgdl: 42.4,
      direction: 'positive', // pushes glucose up
      category: 'lifestyle',
      description: 'Recent 52g carbohydrate ingestion absorbed at 1.8g/min'
    },
    {
      id: 'f2',
      name: 'Insulin on Board (IOB Deficit)',
      impact_mgdl: 24.1,
      direction: 'positive',
      category: 'pharmacology',
      description: 'Active rapid insulin insufficient to match peak glycemic rate'
    },
    {
      id: 'f3',
      name: 'Resting Heart Rate Elevation (Autonomic Stress)',
      impact_mgdl: 6.8,
      direction: 'positive',
      category: 'biometrics',
      description: 'HR elevated to 88 bpm (+16 bpm above resting baseline)'
    },
    {
      id: 'f4',
      name: 'Circadian Basal Drift',
      impact_mgdl: 3.2,
      direction: 'positive',
      category: 'metabolism',
      description: 'Early afternoon physiological insulin sensitivity trough'
    },
    {
      id: 'f5',
      name: 'Residual Physical Exertion',
      impact_mgdl: -10.5,
      direction: 'negative', // lowers glucose
      category: 'lifestyle',
      description: 'Light walking commute 45 minutes prior enhances peripheral uptake'
    }
  ];
}

/**
 * Counterfactual What-If Simulation Engine (Synthetic / Deterministic)
 */
export function simulateCounterfactualResponse(params) {
  const {
    activity_minutes = 20,
    sleep_hours = 1.0,
    carbs_grams = 45,
    insulin_units = 2.0
  } = params;

  // Baseline forecast peak: 198 mg/dL
  const carbDelta = (carbs_grams - 45) * 1.1;
  const insulinDelta = (insulin_units - 0) * -18;
  const activityDelta = (activity_minutes - 0) * -0.55;
  const sleepDelta = (sleep_hours - 0) * -3.5;

  const totalDelta = Math.round(carbDelta + insulinDelta + activityDelta + sleepDelta);
  const simulatedPeak = Math.max(90, Math.min(260, 198 + totalDelta));
  const peakReduction = 198 - simulatedPeak;

  let newRiskTier = 'low';
  if (simulatedPeak > 180) newRiskTier = 'high';
  else if (simulatedPeak > 150) newRiskTier = 'moderate';

  const times = [0, 15, 30, 45, 60, 75, 90, 105, 120];
  const trajectory = times.map((t) => {
    const baseline = Math.round(142 + Math.sin((t / 60) * Math.PI * 0.5) * 56 - (t > 60 ? (t - 60) * 0.8 : 0));
    const factor = Math.sin((t / 60) * Math.PI * 0.5);
    const simulated = Math.max(75, Math.round(142 + (simulatedPeak - 142) * factor - (t > 60 ? (t - 60) * 0.6 : 0)));

    return {
      time_min: t,
      timeLabel: `+${t}m`,
      baseline_glucose: baseline,
      simulated_glucose: simulated
    };
  });

  return {
    baseline_peak_mgdl: 198,
    simulated_peak_mgdl: simulatedPeak,
    peak_reduction_mgdl: peakReduction,
    baseline_tir_pct: 78,
    simulated_tir_pct: Math.min(96, Math.max(50, 78 + Math.round(peakReduction * 0.35))),
    risk_tier_change: {
      before: 'moderate',
      after: newRiskTier
    },
    comparative_trajectory: trajectory
  };
}

/**
 * Realistic Synthetic Clinical Alerts Queue
 */
export const MOCK_ALERTS = [
  {
    id: 'alt-101',
    patient_id: 'GT-9042',
    timestamp: '2026-10-10T14:24:00Z',
    severity: 'critical', // 'critical' | 'warning' | 'info'
    title: 'Impending Hypoglycemia Risk Projected',
    description: 'Metabolic Digital Twin forecasts glucose dropping below 68 mg/dL in ~35 minutes if active IOB continues unchecked.',
    trigger_source: 'Predictive ML Engine',
    clinical_recommendation: 'Evaluate 15g fast-acting oral carbohydrate snack; pause temporary basal.',
    status: 'unacknowledged'
  },
  {
    id: 'alt-102',
    patient_id: 'GT-9042',
    timestamp: '2026-10-10T14:15:00Z',
    severity: 'warning',
    title: 'Postprandial Glycemic Spike Predicted (>195 mg/dL)',
    description: 'Simulated meal absorption exceeds current active insulin on board. Projected peak at 15:30.',
    trigger_source: 'Compartmental Twin Engine',
    clinical_recommendation: 'Consider corrective micro-bolus per patient insulin-to-carb sensitivity ratio.',
    status: 'unacknowledged'
  },
  {
    id: 'alt-103',
    patient_id: 'GT-9042',
    timestamp: '2026-10-10T13:40:00Z',
    severity: 'info',
    title: 'Wearable Sensor Calibration Nominal',
    description: 'Continuous glucose telemetry validated: 99.4% packet integrity with zero drift detected.',
    trigger_source: 'Stage 2 Ingestion Validator',
    clinical_recommendation: 'No action required. Sensor health optimal.',
    status: 'acknowledged'
  },
  {
    id: 'alt-104',
    patient_id: 'GT-8105',
    timestamp: '2026-10-10T12:10:00Z',
    severity: 'warning',
    title: 'Elevated Post-Lunch Excursion Detected',
    description: 'Sensor reading reached 188 mg/dL with delayed autonomic recovery.',
    trigger_source: 'Rule-Based Threshold Engine',
    clinical_recommendation: 'Encourage 20-minute postprandial light ambulation.',
    status: 'acknowledged'
  }
];

/**
 * Digital Twin Engine State Metadata
 */
export function getMockTwinStatus(patientId = 'GT-9042') {
  return {
    patient_id: patientId,
    engine_state: 'synchronized',
    latency_ms: 12,
    last_calibration_time: '2026-10-10T14:00:00Z',
    model_architecture: 'Multi-Compartment PK/PD + LightGBM Residual',
    active_iob_units: 1.25,
    active_cob_grams: 34.8,
    metabolic_drift_score: 0.038,
    data_quality_pct: 99.4,
    wearable_battery_pct: 88,
    sensor_drift_status: 'Nominal'
  };
}
