'use strict'

import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node'
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-proto'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-proto'
import { resourceFromAttributes } from '@opentelemetry/resources'
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics'
import { NodeSDK } from '@opentelemetry/sdk-node'
import { ATTR_SERVICE_NAME } from '@opentelemetry/semantic-conventions'
import process from 'process'

// Add otel logging when debugging
// import { diag, DiagConsoleLogger, DiagLogLevel } from '@opentelemetry/api';
// diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.DEBUG);

const serviceName = `${process.env.NEXT_PUBLIC_CI_PROJECT_NAME}-fe`
const tracesEndpoint = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
const metricsEndpoint = process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT

const traceExporter = new OTLPTraceExporter({ url: tracesEndpoint })
const metricReader = new PeriodicExportingMetricReader({
  exporter: new OTLPMetricExporter({
    url: metricsEndpoint,
  }),
})

const sdk = new NodeSDK({
  traceExporter,
  metricReader,
  instrumentations: [getNodeAutoInstrumentations()],
  resource: resourceFromAttributes({
    [ATTR_SERVICE_NAME]: serviceName,
  }),
})

// initialize the SDK and register with the OpenTelemetry API
// this enables the API to record telemetry
sdk.start()

console.log(
  `OTEL service ${serviceName} started with tracesEndpoint ${tracesEndpoint} and metricsEndpoint ${metricsEndpoint} `
)

// gracefully shut down the SDK on process exit
process.on('SIGTERM', () => {
  sdk
    .shutdown()
    .then(() => console.log('Tracing terminated'))
    .catch((error) => console.log('Error terminating tracing', error))
    .finally(() => process.exit(0))
})
