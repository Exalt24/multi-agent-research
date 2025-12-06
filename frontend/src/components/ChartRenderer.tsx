"use client";

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartType,
} from "chart.js";
import { Bar, Line, Pie, Doughnut } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

interface ChartData {
  id?: string;
  type: ChartType | string;
  title: string;
  description?: string;
  data?: {
    labels: string[];
    datasets: {
      label: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string | string[];
      borderWidth?: number;
    }[];
  };
  options?: ChartOptions<ChartType>;
}

interface ChartRendererProps {
  chart: ChartData;
}

export default function ChartRenderer({ chart }: ChartRendererProps) {
  // Default options for all charts
  const defaultOptions: ChartOptions<ChartType> = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          color: "#e5e7eb", // gray-200
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: chart.title,
        color: "#f3f4f6", // gray-100
        font: {
          size: 16,
          weight: "bold" as const,
        },
      },
      tooltip: {
        backgroundColor: "rgba(31, 41, 55, 0.9)", // gray-800
        titleColor: "#f3f4f6",
        bodyColor: "#e5e7eb",
        borderColor: "#4b5563",
        borderWidth: 1,
      },
    },
    scales:
      chart.type !== "pie" && chart.type !== "doughnut"
        ? {
            x: {
              ticks: {
                color: "#9ca3af", // gray-400
              },
              grid: {
                color: "rgba(75, 85, 99, 0.2)", // gray-600 with opacity
              },
            },
            y: {
              ticks: {
                color: "#9ca3af",
              },
              grid: {
                color: "rgba(75, 85, 99, 0.2)",
              },
            },
          }
        : undefined,
  };

  const safeData =
    chart.data ?? {
      labels: [],
      datasets: [],
    };

  // Merge with custom options from agent
  const finalOptions: ChartOptions<ChartType> = {
    ...defaultOptions,
    ...chart.options,
  };

  // Render the appropriate chart type
  const renderChart = () => {
    switch (chart.type) {
      case "bar":
        return <Bar data={safeData} options={finalOptions as ChartOptions<"bar">} />;
      case "line":
        return <Line data={safeData} options={finalOptions as ChartOptions<"line">} />;
      case "pie":
        return <Pie data={safeData} options={finalOptions as ChartOptions<"pie">} />;
      case "doughnut":
        return <Doughnut data={safeData} options={finalOptions as ChartOptions<"doughnut">} />;
      default:
        return (
          <div className="text-red-400">
            Unsupported chart type: {chart.type}
          </div>
        );
    }
  };

  return (
    <div className="bg-gray-900/50 rounded-lg p-6 border border-gray-700">
      {/* Chart */}
      <div className="mb-3">{renderChart()}</div>

      {/* Description */}
      {chart.description && (
        <p className="text-sm text-gray-400 mt-4">{chart.description}</p>
      )}
    </div>
  );
}
