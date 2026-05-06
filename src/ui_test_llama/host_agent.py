# TOKENIZERS_PARALLELISM=True CUDA_VISIBLE_DEVICES=0,1,2,3 vllm serve Qwen/Qwen2.5-VL-72B-Instruct --port 11111 --served-model-name qwen-vl-model --tensor-parallel-size 4 --max-model-len 48000 --max-num-seqs 16 --limit-mm-per-prompt "image=2, video=1"
# Set environment variables for better memory management
from openai import OpenAI
import base64

# Function to encode the image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Set OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = "http://127.0.0.1:11111/v1"

client = OpenAI(
    api_key=openai_api_key, 
    base_url=openai_api_base,
)


code_scripts = """
import type React from "react";
import { useState, useEffect, useRef } from "react";
import { Search, Download, ChevronDown, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import {
  LineChart,
  XAxis,
  YAxis,
  Line,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

interface StockData {
  code: string;
  name: string;
  price: number;
  change: number;
  volume: number;
  marketCap: string;
  pe: number;
  pb: number;
  dividendYield: number;
  eps: number;
  revenue: string;
  netIncome: string;
  ebitda: string;
  grossMargin: number;
  operatingMargin: number;
  netMargin: number;
}

interface HistoricalData {
  date: string;
  price: number;
  volume: number;
}

interface FinancialMetric {
  year: string;
  revenue: number;
  netIncome: number;
  ebitda: number;
  grossMargin: number;
  operatingMargin: number;
  netMargin: number;
}

interface Distribution {
  name: string;
  value: number;
}

const stockData: Record<string, StockData> = {
  AAPL: {
    code: "AAPL",
    name: "Apple Inc.",
    price: 150.23,
    change: 0.5,
    volume: 45000000,
    marketCap: "2.3T",
    pe: 25.6,
    pb: 8.5,
    dividendYield: 0.56,
    eps: 5.89,
    revenue: "365B",
    netIncome: "95B",
    ebitda: "120B",
    grossMargin: 43.8,
    operatingMargin: 30.5,
    netMargin: 25.9,
  },
  MSFT: {
    code: "MSFT",
    name: "Microsoft Corporation",
    price: 280.15,
    change: -0.2,
    volume: 32000000,
    marketCap: "2.1T",
    pe: 30.2,
    pb: 10.3,
    dividendYield: 0.72,
    eps: 9.28,
    revenue: "245B",
    netIncome: "72B",
    ebitda: "95B",
    grossMargin: 36.5,
    operatingMargin: 35.2,
    netMargin: 31.4,
  },
  GOOGL: {
    code: "GOOGL",
    name: "Alphabet Inc.",
    price: 132.88,
    change: 0.8,
    volume: 28000000,
    marketCap: "1.7T",
    pe: 24.9,
    pb: 6.8,
    dividendYield: 0,
    eps: 5.34,
    revenue: "305B",
    netIncome: "60B",
    ebitda: "85B",
    grossMargin: 57.2,
    operatingMargin: 28.4,
    netMargin: 21.5,
  },
  AMZN: {
    code: "AMZN",
    name: "Amazon.com Inc.",
    price: 134.52,
    change: 0.4,
    volume: 38000000,
    marketCap: "1.8T",
    pe: 55.3,
    pb: 9.5,
    dividendYield: 0,
    eps: 2.43,
    revenue: "470B",
    netIncome: "33B",
    ebitda: "65B",
    grossMargin: 43.5,
    operatingMargin: 5.9,
    netMargin: 3.8,
  },
  TSLA: {
    code: "TSLA",
    name: "Tesla Inc.",
    price: 245.67,
    change: -1.2,
    volume: 42000000,
    marketCap: "980B",
    pe: 65.2,
    pb: 15.6,
    dividendYield: 0,
    eps: 3.77,
    revenue: "96B",
    netIncome: "12.5B",
    ebitda: "18B",
    grossMargin: 27.3,
    operatingMargin: 12.4,
    netMargin: 10.5,
  },
  META: {
    code: "META",
    name: "Meta Platforms Inc.",
    price: 340.56,
    change: 1.5,
    volume: 22000000,
    marketCap: "1.2T",
    pe: 22.8,
    pb: 6.2,
    dividendYield: 0,
    eps: 14.92,
    revenue: "134B",
    netIncome: "39B",
    ebitda: "50B",
    grossMargin: 81.3,
    operatingMargin: 35.5,
    netMargin: 28.6,
  },
  NVDA: {
    code: "NVDA",
    name: "NVIDIA Corporation",
    price: 865.43,
    change: 2.3,
    volume: 35000000,
    marketCap: "2.2T",
    pe: 85.3,
    pb: 25.5,
    dividendYield: 0.12,
    eps: 10.14,
    revenue: "26.9B",
    netIncome: "29.7B",
    ebitda: "35B",
    grossMargin: 72.8,
    operatingMargin: 64.9,
    netMargin: 55.6,
  },
  NFLX: {
    code: "NFLX",
    name: "Netflix Inc.",
    price: 625.45,
    change: 0.9,
    volume: 18000000,
    marketCap: "290B",
    pe: 45.2,
    pb: 12.8,
    dividendYield: 0,
    eps: 13.82,
    revenue: "32B",
    netIncome: "5.4B",
    ebitda: "7.5B",
    grossMargin: 44.3,
    operatingMargin: 22.4,
    netMargin: 18.5,
  },
};

const historicalData: Record<string, HistoricalData[]> = {
  AAPL: [
    { date: "2023-01", price: 128.53, volume: 40000000 },
    { date: "2023-02", price: 132.45, volume: 38000000 },
    { date: "2023-03", price: 135.89, volume: 42000000 },
    { date: "2023-04", price: 140.23, volume: 45000000 },
    { date: "2023-05", price: 138.56, volume: 32000000 },
    { date: "2023-06", price: 142.87, volume: 35000000 },
    { date: "2023-07", price: 145.32, volume: 37000000 },
    { date: "2023-08", price: 148.76, volume: 43000000 },
    { date: "2023-09", price: 152.43, volume: 46000000 },
    { date: "2023-10", price: 150.23, volume: 45000000 },
  ],
  MSFT: [
    { date: "2023-01", price: 255.23, volume: 28000000 },
    { date: "2023-02", price: 262.45, volume: 30000000 },
    { date: "2023-03", price: 265.89, volume: 32000000 },
    { date: "2023-04", price: 270.23, volume: 34000000 },
    { date: "2023-05", price: 268.56, volume: 29000000 },
    { date: "2023-06", price: 272.87, volume: 31000000 },
    { date: "2023-07", price: 275.32, volume: 33000000 },
    { date: "2023-08", price: 278.76, volume: 36000000 },
    { date: "2023-09", price: 282.43, volume: 38000000 },
    { date: "2023-10", price: 280.15, volume: 32000000 },
  ],
  GOOGL: [
    { date: "2023-01", price: 120.53, volume: 25000000 },
    { date: "2023-02", price: 125.45, volume: 27000000 },
    { date: "2023-03", price: 128.89, volume: 28000000 },
    { date: "2023-04", price: 130.23, volume: 29000000 },
    { date: "2023-05", price: 128.56, volume: 26000000 },
    { date: "2023-06", price: 132.87, volume: 28000000 },
    { date: "2023-07", price: 135.32, volume: 30000000 },
    { date: "2023-08", price: 138.76, volume: 31000000 },
    { date: "2023-09", price: 142.43, volume: 33000000 },
    { date: "2023-10", price: 132.88, volume: 28000000 },
  ],
  AMZN: [
    { date: "2023-01", price: 125.23, volume: 35000000 },
    { date: "2023-02", price: 128.45, volume: 37000000 },
    { date: "2023-03", price: 130.89, volume: 38000000 },
    { date: "2023-04", price: 135.23, volume: 40000000 },
    { date: "2023-05", price: 132.56, volume: 36000000 },
    { date: "2023-06", price: 138.87, volume: 39000000 },
    { date: "2023-07", price: 140.32, volume: 41000000 },
    { date: "2023-08", price: 142.76, volume: 42000000 },
    { date: "2023-09", price: 145.43, volume: 44000000 },
    { date: "2023-10", price: 134.52, volume: 38000000 },
  ],
  TSLA: [
    { date: "2023-01", price: 220.53, volume: 40000000 },
    { date: "2023-02", price: 225.45, volume: 42000000 },
    { date: "2023-03", price: 230.89, volume: 44000000 },
    { date: "2023-04", price: 235.23, volume: 46000000 },
    { date: "2023-05", price: 230.56, volume: 38000000 },
    { date: "2023-06", price: 240.87, volume: 45000000 },
    { date: "2023-07", price: 245.32, volume: 47000000 },
    { date: "2023-08", price: 250.76, volume: 49000000 },
    { date: "2023-09", price: 255.43, volume: 51000000 },
    { date: "2023-10", price: 245.67, volume: 42000000 },
  ],
  META: [
    { date: "2023-01", price: 310.53, volume: 20000000 },
    { date: "2023-02", price: 315.45, volume: 22000000 },
    { date: "2023-03", price: 320.89, volume: 24000000 },
    { date: "2023-04", price: 325.23, volume: 26000000 },
    { date: "2023-05", price: 320.56, volume: 21000000 },
    { date: "2023-06", price: 330.87, volume: 23000000 },
    { date: "2023-07", price: 335.32, volume: 25000000 },
    { date: "2023-08", price: 340.76, volume: 27000000 },
    { date: "2023-09", price: 345.43, volume: 29000000 },
    { date: "2023-10", price: 340.56, volume: 22000000 },
  ],
  NVDA: [
    { date: "2023-01", price: 750.53, volume: 30000000 },
    { date: "2023-02", price: 765.45, volume: 32000000 },
    { date: "2023-03", price: 780.89, volume: 34000000 },
    { date: "2023-04", price: 795.23, volume: 36000000 },
    { date: "2023-05", price: 790.56, volume: 31000000 },
    { date: "2023-06", price: 805.87, volume: 33000000 },
    { date: "2023-07", price: 820.32, volume: 35000000 },
    { date: "2023-08", price: 835.76, volume: 37000000 },
    { date: "2023-09", price: 850.43, volume: 39000000 },
    { date: "2023-10", price: 865.43, volume: 35000000 },
  ],
  NFLX: [
    { date: "2023-01", price: 550.53, volume: 15000000 },
    { date: "2023-02", price: 565.45, volume: 17000000 },
    { date: "2023-03", price: 580.89, volume: 19000000 },
    { date: "2023-04", price: 595.23, volume: 20000000 },
    { date: "2023-05", price: 590.56, volume: 16000000 },
    { date: "2023-06", price: 605.87, volume: 18000000 },
    { date: "2023-07", price: 620.32, volume: 19000000 },
    { date: "2023-08", price: 635.76, volume: 21000000 },
    { date: "2023-09", price: 650.43, volume: 23000000 },
    { date: "2023-10", price: 625.45, volume: 18000000 },
  ],
};

const financialMetrics: Record<string, FinancialMetric[]> = {
  AAPL: [
    {
      year: "2020",
      revenue: 274.5,
      netIncome: 57.4,
      ebitda: 77.3,
      grossMargin: 38.2,
      operatingMargin: 24.9,
      netMargin: 20.9,
    },
    {
      year: "2021",
      revenue: 365.8,
      netIncome: 95.0,
      ebitda: 120.2,
      grossMargin: 41.8,
      operatingMargin: 29.2,
      netMargin: 25.9,
    },
    {
      year: "2022",
      revenue: 394.3,
      netIncome: 95.0,
      ebitda: 125.4,
      grossMargin: 43.8,
      operatingMargin: 30.5,
      netMargin: 24.0,
    },
  ],
  MSFT: [
    {
      year: "2020",
      revenue: 231.8,
      netIncome: 61.3,
      ebitda: 85.4,
      grossMargin: 35.9,
      operatingMargin: 32.4,
      netMargin: 30.1,
    },
    {
      year: "2021",
      revenue: 168.1,
      netIncome: 39.2,
      ebitda: 53.6,
      grossMargin: 36.1,
      operatingMargin: 28.5,
      netMargin: 23.3,
    },
    {
      year: "2022",
      revenue: 198.3,
      netIncome: 72.7,
      ebitda: 95.1,
      grossMargin: 36.5,
      operatingMargin: 35.2,
      netMargin: 31.4,
    },
  ],
  GOOGL: [
    {
      year: "2020",
      revenue: 161.8,
      netIncome: 40.3,
      ebitda: 55.8,
      grossMargin: 56.2,
      operatingMargin: 28.9,
      netMargin: 22.5,
    },
    {
      year: "2021",
      revenue: 257.6,
      netIncome: 76.0,
      ebitda: 102.3,
      grossMargin: 56.8,
      operatingMargin: 30.2,
      netMargin: 29.5,
    },
    {
      year: "2022",
      revenue: 305.6,
      netIncome: 60.0,
      ebitda: 85.4,
      grossMargin: 57.2,
      operatingMargin: 28.4,
      netMargin: 21.5,
    },
  ],
  AMZN: [
    {
      year: "2020",
      revenue: 386.1,
      netIncome: 21.3,
      ebitda: 48.2,
      grossMargin: 42.8,
      operatingMargin: 5.6,
      netMargin: 3.5,
    },
    {
      year: "2021",
      revenue: 478.7,
      netIncome: 33.4,
      ebitda: 65.2,
      grossMargin: 43.5,
      operatingMargin: 5.9,
      netMargin: 3.8,
    },
    {
      year: "2022",
      revenue: 514.3,
      netIncome: 18.7,
      ebitda: 54.8,
      grossMargin: 45.3,
      operatingMargin: 3.2,
      netMargin: 2.1,
    },
  ],
  TSLA: [
    {
      year: "2020",
      revenue: 31.5,
      netIncome: 0.7,
      ebitda: 4.5,
      grossMargin: 25.7,
      operatingMargin: 6.3,
      netMargin: 2.3,
    },
    {
      year: "2021",
      revenue: 53.8,
      netIncome: 5.5,
      ebitda: 9.4,
      grossMargin: 26.2,
      operatingMargin: 14.5,
      netMargin: 10.2,
    },
    {
      year: "2022",
      revenue: 81.5,
      netIncome: 12.5,
      ebitda: 18.2,
      grossMargin: 27.3,
      operatingMargin: 16.4,
      netMargin: 15.3,
    },
  ],
  META: [
    {
      year: "2020",
      revenue: 85.9,
      netIncome: 29.1,
      ebitda: 42.1,
      grossMargin: 81.2,
      operatingMargin: 38.9,
      netMargin: 33.9,
    },
    {
      year: "2021",
      revenue: 117.9,
      netIncome: 39.4,
      ebitda: 54.2,
      grossMargin: 80.5,
      operatingMargin: 39.6,
      netMargin: 33.4,
    },
    {
      year: "2022",
      revenue: 134.9,
      netIncome: 23.2,
      ebitda: 35.4,
      grossMargin: 81.3,
      operatingMargin: 35.5,
      netMargin: 17.2,
    },
  ],
  NVDA: [
    {
      year: "2020",
      revenue: 10.9,
      netIncome: 2.8,
      ebitda: 4.3,
      grossMargin: 64.5,
      operatingMargin: 27.5,
      netMargin: 25.5,
    },
    {
      year: "2021",
      revenue: 26.9,
      netIncome: 9.8,
      ebitda: 14.2,
      grossMargin: 66.2,
      operatingMargin: 37.5,
      netMargin: 36.4,
    },
    {
      year: "2022",
      revenue: 26.9,
      netIncome: 4.3,
      ebitda: 8.5,
      grossMargin: 72.8,
      operatingMargin: 42.5,
      netMargin: 16.1,
    },
  ],
  NFLX: [
    {
      year: "2020",
      revenue: 20.0,
      netIncome: 2.8,
      ebitda: 4.6,
      grossMargin: 44.5,
      operatingMargin: 18.5,
      netMargin: 14.0,
    },
    {
      year: "2021",
      revenue: 29.7,
      netIncome: 5.1,
      ebitda: 8.5,
      grossMargin: 44.3,
      operatingMargin: 20.2,
      netMargin: 17.2,
    },
    {
      year: "2022",
      revenue: 31.9,
      netIncome: 4.8,
      ebitda: 7.4,
      grossMargin: 44.3,
      operatingMargin: 21.4,
      netMargin: 15.0,
    },
  ],
};

const ownershipDistribution: Record<string, Distribution[]> = {
  AAPL: [
    { name: "Institutional Investors", value: 60 },
    { name: "Retail Investors", value: 30 },
    { name: "Insiders", value: 10 },
  ],
  MSFT: [
    { name: "Institutional Investors", value: 70 },
    { name: "Retail Investors", value: 20 },
    { name: "Insiders", value: 10 },
  ],
  GOOGL: [
    { name: "Institutional Investors", value: 65 },
    { name: "Retail Investors", value: 25 },
    { name: "Insiders", value: 10 },
  ],
  AMZN: [
    { name: "Institutional Investors", value: 55 },
    { name: "Retail Investors", value: 35 },
    { name: "Insiders", value: 10 },
  ],
  TSLA: [
    { name: "Institutional Investors", value: 50 },
    { name: "Retail Investors", value: 40 },
    { name: "Insiders", value: 10 },
  ],
  META: [
    { name: "Institutional Investors", value: 75 },
    { name: "Retail Investors", value: 15 },
    { name: "Insiders", value: 10 },
  ],
  NVDA: [
    { name: "Institutional Investors", value: 70 },
    { name: "Retail Investors", value: 20 },
    { name: "Insiders", value: 10 },
  ],
  NFLX: [
    { name: "Institutional Investors", value: 65 },
    { name: "Retail Investors", value: 25 },
    { name: "Insiders", value: 10 },
  ],
};

const colorScheme = {
  navy: "#0B3D91",
  lighterNavy: "#2c5ba9",
  skyBlue: "#7fb7e1",
  lighterSkyBlue: "#c7e1f7",
  lightGray: "#f5f5f5",
  darkGray: "#4a5568",
  mediumGray: "#a0aec0",
  white: "#ffffff",
  black: "#000000",
  green: "#48BB78",
  red: "#F56565",
};

const customTooltipStyle = {
  color: colorScheme.black,
  fontSize: 14,
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        className="custom-tooltip"
        style={{
          backgroundColor: colorScheme.white,
          border: `1px solid ${colorScheme.skyBlue}`,
          borderRadius: "4px",
          padding: "10px",
          boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        }}
      >
        <p className="label" style={{ color: colorScheme.black }}>
          {`${label}: ${payload[0].value}`}
        </p>
        {payload.map((entry: any, index: number) => (
          <p
            key={index}
            style={{
              color: entry.color || colorScheme.black,
              margin: "5px 0",
            }}
          >
            {`${entry.name}: ${entry.value}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function StockReport() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStock, setSelectedStock] = useState("AAPL");
  const [reportFormat, setReportFormat] = useState("summary");
  const [reportContent, setReportContent] = useState<string[]>([
    "overview",
    "financials",
  ]);
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isClient, setIsClient] = useState(false);

  const filteredStocks = Object.values(stockData).filter(
    (stock) =>
      stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const downloadReport = () => {
    const content = `
  Stock Report: ${stockData[selectedStock].name} (${stockData[selectedStock].code})
  Report Date: ${new Date().toLocaleDateString()}
  
  ${
    reportContent.includes("overview") ? "Overview:\n" : ""
  }  Price: $${stockData[selectedStock].price}
  ${
    reportContent.includes("overview") ? "Change: " : ""
  }${stockData[selectedStock].change}%
  ${
    reportContent.includes("overview") ? "Volume: " : ""
  }${stockData[selectedStock].volume.toLocaleString()}
  ${
    reportContent.includes("overview") ? "Market Cap: " : ""
  }${stockData[selectedStock].marketCap}
  
  ${
    reportContent.includes("financials") ? "Financials:\n" : ""
  }  Revenue: ${stockData[selectedStock].revenue}
  ${
    reportContent.includes("financials") ? "Net Income: " : ""
  }${stockData[selectedStock].netIncome}
  ${
    reportContent.includes("financials") ? "EBITDA: " : ""
  }${stockData[selectedStock].ebitda}
  ${
    reportContent.includes("financials") ? "Gross Margin: " : ""
  }${stockData[selectedStock].grossMargin}%
  ${
    reportContent.includes("financials") ? "Operating Margin: " : ""
  }${stockData[selectedStock].operatingMargin}%
  ${
    reportContent.includes("financials") ? "Net Margin: " : ""
  }${stockData[selectedStock].netMargin}%
  
  ${
    reportContent.includes("valuation") ? "Valuation:\n" : ""
  }  P/E Ratio: ${stockData[selectedStock].pe}
  ${
    reportContent.includes("valuation") ? "P/B Ratio: " : ""
  }${stockData[selectedStock].pb}
  ${
    reportContent.includes("valuation") ? "Dividend Yield: " : ""
  }${stockData[selectedStock].dividendYield}%
  ${
    reportContent.includes("valuation") ? "EPS: " : ""
  }${stockData[selectedStock].eps}
  
  Historical Data:
  ${historicalData[selectedStock]
    .map((data) => `${data.date}: $${data.price}`)
    .join("\n")}
  
  Financial Metrics:
  ${financialMetrics[selectedStock]
    .map(
      (data) =>
        `${data.year}: Revenue $${data.revenue}B, Net Income $${data.netIncome}B`
    )
    .join("\n")}
  
  Ownership Distribution:
  ${ownershipDistribution[selectedStock]
    .map((data) => `${data.name}: ${data.value}%`)
    .join("\n")}
  `;

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `stock_report_${selectedStock}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const toggleReportContent = (content: string) => {
    setReportContent((prev) =>
      prev.includes(content)
        ? prev.filter((item) => item !== content)
        : [...prev, content]
    );
  };

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return <div className="h-screen w-screen bg-white"></div>;
  }

  return (
    <div
      className="min-h-screen w-full p-3 sm:p-4 md:p-6 lg:p-8"
      style={{ backgroundColor: colorScheme.white }}
    >
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-4 md:flex-row md:justify-between md:items-center">
          <h1
            className="text-xl sm:text-2xl font-bold"
            style={{ color: colorScheme.navy }}
          >
            Stock Report Generator
          </h1>

          <div className="flex flex-wrap gap-2 sm:flex-nowrap sm:gap-3">
            <div className="relative flex-grow sm:basis-1/3 md:basis-1/4">
              <Select value={selectedStock} onValueChange={setSelectedStock}>
                <SelectTrigger
                  className="h-9 w-full text-sm"
                  style={{
                    backgroundColor: colorScheme.skyBlue,
                    borderColor: colorScheme.navy,
                    color: colorScheme.navy,
                  }}
                >
                  <SelectValue placeholder="Select stock" />
                </SelectTrigger>
                <SelectContent>
                  {Object.keys(stockData).map((code) => (
                    <SelectItem key={code} value={code}>
                      {stockData[code].name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="relative flex-grow sm:basis-1/3 md:basis-1/4">
              <Select value={reportFormat} onValueChange={setReportFormat}>
                <SelectTrigger
                  className="h-9 w-full text-sm"
                  style={{
                    backgroundColor: colorScheme.skyBlue,
                    borderColor: colorScheme.navy,
                    color: colorScheme.navy,
                  }}
                >
                  <SelectValue placeholder="Report format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="summary">Summary</SelectItem>
                  <SelectItem value="detailed">Detailed</SelectItem>
                  <SelectItem value="extended">Extended</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              className="h-9 px-3 text-sm"
              onClick={downloadReport}
              style={{
                backgroundColor: colorScheme.navy,
                color: colorScheme.white,
              }}
            >
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle
                className="text-base"
                style={{ color: colorScheme.navy }}
              >
                Stock Information
              </CardTitle>
              <CardDescription>
                {stockData[selectedStock].name}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-medium">Price</h3>
                  <p
                    className="text-lg font-semibold"
                    style={{ color: colorScheme.navy }}
                  >
                    ${stockData[selectedStock].price}
                  </p>
                </div>
                <div>
                  <h3 className="font-medium">Change</h3>
                  <p
                    className="text-lg font-semibold"
                    style={{
                      color:
                        stockData[selectedStock].change >= 0
                          ? colorScheme.green
                          : colorScheme.red,
                    }}
                  >
                    {stockData[selectedStock].change >= 0 ? "+" : ""}
                    {stockData[selectedStock].change}%
                  </p>
                </div>
                <div>
                  <h3 className="font-medium">Volume</h3>
                  <p className="text-sm">
                    {stockData[selectedStock].volume.toLocaleString()}
                  </p>
                </div>
                <div>
                  <h3 className="font-medium">Market Cap</h3>
                  <p className="text-sm">
                    {stockData[selectedStock].marketCap}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle
                className="text-base"
                style={{ color: colorScheme.navy }}
              >
                Historical Data
              </CardTitle>
              <CardDescription>Price and volume over time</CardDescription>
            </CardHeader>
            <CardContent className="h-[250px] w-full">
              <ResponsiveContainer
                width="100%"
                height="100%"
                className="bg-white"
              >
                <AreaChart
                  data={historicalData[selectedStock]}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient
                      id="colorPrice"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="5%"
                        stopColor={colorScheme.skyBlue}
                        stopOpacity={0.8}
                      />
                      <stop
                        offset="95%"
                        stopColor={colorScheme.skyBlue}
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="date"
                    tick={{ fill: colorScheme.darkGray }}
                    axisLine={{
                      stroke: colorScheme.lightGray,
                    }}
                    tickLine={{ stroke: colorScheme.lightGray }}
                  />
                  <YAxis
                    tick={{ fill: colorScheme.darkGray }}
                    axisLine={{
                      stroke: colorScheme.lightGray,
                    }}
                    tickLine={{ stroke: colorScheme.lightGray }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="price"
                    stroke={colorScheme.navy}
                    fillOpacity={1}
                    fill="url(#colorPrice)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle
                className="text-base"
                style={{ color: colorScheme.navy }}
              >
                Financial Metrics
              </CardTitle>
              <CardDescription>Key financial indicators</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Metric
                    </TableHead>
                    <TableHead
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Value
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      P/E Ratio
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].pe}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      P/B Ratio
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].pb}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Dividend Yield
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].dividendYield}%
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      EPS
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].eps}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle
                className="text-base"
                style={{ color: colorScheme.navy }}
              >
                Financial Summary
              </CardTitle>
              <CardDescription>Revenue and income data</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Metric
                    </TableHead>
                    <TableHead
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Value
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Revenue
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].revenue}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Net Income
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].netIncome}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      EBITDA
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].ebitda}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.darkGray }}
                    >
                      Gross Margin
                    </TableCell>
                    <TableCell
                      className="text-xs"
                      style={{ color: colorScheme.navy }}
                    >
                      {stockData[selectedStock].grossMargin}%
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card className="md:col-span-1">
            <CardHeader>
              <CardTitle
                className="text-base"
                style={{ color: colorScheme.navy }}
              >
                Ownership Distribution
              </CardTitle>
              <CardDescription>Investor breakdown</CardDescription>
            </CardHeader>
            <CardContent className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ownershipDistribution[selectedStock]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                  >
                    {ownershipDistribution[selectedStock].map(
                      (entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            index === 0
                              ? colorScheme.navy
                              : index === 1
                              ? colorScheme.skyBlue
                              : colorScheme.lighterSkyBlue
                          }
                        />
                      )
                    )}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend layout="vertical" align="right" verticalAlign="middle" />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle
              className="text-base"
              style={{ color: colorScheme.navy }}
            >
              Stock Performance
            </CardTitle>
            <CardDescription>Price trend over time</CardDescription>
          </CardHeader>
          <CardContent className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={historicalData[selectedStock]}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={colorScheme.lightGray}
                />
                <XAxis
                  dataKey="date"
                  tick={{ fill: colorScheme.darkGray }}
                  axisLine={{ stroke: colorScheme.lightGray }}
                  tickLine={{ stroke: colorScheme.lightGray }}
                />
                <YAxis
                  domain={["dataMin - 5", "dataMax + 5"]}
                  tick={{ fill: colorScheme.darkGray }}
                  axisLine={{ stroke: colorScheme.lightGray }}
                  tickLine={{ stroke: colorScheme.lightGray }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke={colorScheme.navy}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 6, fill: colorScheme.navy }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle
              className="text-base"
              style={{ color: colorScheme.navy }}
            >
              Report Customization
            </CardTitle>
            <CardDescription>Select content for your report</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="overview"
                  checked={reportContent.includes("overview")}
                  onChange={() => toggleReportContent("overview")}
                  className="h-4 w-4 rounded border-gray-300"
                  style={{ accentColor: colorScheme.navy }}
                />
                <label
                  htmlFor="overview"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  style={{ color: colorScheme.navy }}
                >
                  Overview
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="financials"
                  checked={reportContent.includes("financials")}
                  onChange={() => toggleReportContent("financials")}
                  className="h-4 w-4 rounded border-gray-300"
                  style={{ accentColor: colorScheme.navy }}
                />
                <label
                  htmlFor="financials"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  style={{ color: colorScheme.navy }}
                >
                  Financials
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="valuation"
                  checked={reportContent.includes("valuation")}
                  onChange={() => toggleReportContent("valuation")}
                  className="h-4 w-4 rounded border-gray-300"
                  style={{ accentColor: colorScheme.navy }}
                />
                <label
                  htmlFor="valuation"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  style={{ color: colorScheme.navy }}
                >
                  Valuation
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="metrics"
                  checked={reportContent.includes("metrics")}
                  onChange={() => toggleReportContent("metrics")}
                  className="h-4 w-4 rounded border-gray-300"
                  style={{ accentColor: colorScheme.navy }}
                />
                <label
                  htmlFor="metrics"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  style={{ color: colorScheme.navy }}
                >
                  Metrics
                </label>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button
              className="text-sm"
              onClick={downloadReport}
              style={{ backgroundColor: colorScheme.navy }}
            >
              <Download className="mr-2 h-4 w-4" />
              Download Report
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
"""

instructions = """Please implement a website for generating stock reports to provide stock information and analysis. The website should have the functionality to search and summarize stock information, and generate customized stock reports based on user requirements. Users should be able to input stock codes or names, select report formats and content, and the website will automatically generate the corresponding reports. The reports should include basic stock information, market trends, financial data, and more. Set the background color to white and the component color to navy."""


code_samples = """ 
                python
                from selenium import webdriver

                def test_generate_custom_report():
                    driver = webdriver.Chrome()
                    driver.get("http://example-stock-report.com")
                    
                    search_bar = driver.find_element_by_name("search")
                    search_bar.clear()
                    search_bar.send_keys("GOOGL")
                    search_bar.send_keys(Keys.RETURN)
                    
                    format_option = driver.find_element_by_id("report_format")
                    format_option.click()
                    
                    content_option = driver.find_element_by_id("report_content")
                    content_option.click()
                    
                    generate_button = driver.find_element_by_id("generate_report")
                    generate_button.click()
                    
                    assert "Google LLC" in driver.page_source and "Selected Format" in driver.page_source and "Selected Content" in driver.page_source
                    
                    driver.quit()

                test_generate_custom_report()
                """

# print("Chat response:", response_content)


# First try with a simple text-only request to test if the server is working properly

print("Testing connection with a simple text-only request...")
chat_response = client.chat.completions.create(
model="qwen-vl-model",
messages=[
    {"role": "system", "content": "You are an expert AI assistant and exceptional senior software developer with vast knowledge across multiple programming languages, frameworks, and best practices."},
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{encode_image('results/results/task000001-1_0/screenshot1.png')}"
                }
            },
            {"type": "text", "text": "Given instructions: \"" + instructions + "\" , a code script of website template \"" + code_scripts + "\"which are for generating the website, and single image of website template. Now, as a test engineer, you should generate comprehensive test cases across three key dimensions:\n\n1. Functionality Testing: Test core user interactions and features like search, report generation, and customization options.\n2. Data Display Testing: Verify that stock information, charts, financial data, and reports are displayed correctly and accurately.\n3. Design Validation Testing: Confirm that UI elements follow the specified design requirements (white background, navy components) and provide good user experience.\n\nFor each dimension, create at least two detailed test cases (total of 6 or more). For each test case, provide:\n- Test case ID and descriptive name\n- Test objective\n- Preconditions: For all test cases, the standard precondition is that the website is up and running. Each test should start from the beginning (opening the website) rather than depending on previous test states.\n- Step-by-step test procedure: Always start with opening the website in a browser.\n- Expected results\n"},
        ],
    },
],

)

response_content = chat_response.choices[0].message.content
print("Chat response:", response_content)


chat_response = client.chat.completions.create(
    model="qwen-vl-model",
    messages=[
        {"role": "system", "content": "You are an expert AI assistant and exceptional senior software developer with vast knowledge across multiple programming languages, frameworks, and best practices."},
        {
            "role": "user",
            "content": [
              
                {"type": "text", "text": "Generate complete Python Selenium test code for ALL test cases described below: \"" + response_content + "\". You MUST refer to the code script of website template \"" + code_scripts + "\ for carefully design each test function. For EACH test case, write a separate, complete Python function using Selenium WebDriver that implements the test case. Include proper assertions, error handling, and detailed comments for each step. Name each function according to its test case ID (e.g., test_ft_01 for FT-01, test_dd_01 for DD-01). Do not include any placeholders or comments suggesting additional functions to be added later. Provide the FULL implementation for ALL test cases mentioned."},
            ],
        },
    ],
)

response_content_for_testing_code = chat_response.choices[0].message.content
print("Chat response for testing code:", response_content_for_testing_code)



# Extract Python code blocks from the response
import re

def extract_test_cases(response_text):
    # Find all Python code blocks in the response
    code_blocks = re.findall(r'```python\n([\s\S]*?)\n```', response_text)
    
    # If no code blocks found, try without the language specifier
    if not code_blocks:
        code_blocks = re.findall(r'```\n([\s\S]*?)\n```', response_text)
    
    # If no code blocks found, check if the entire text might be Python code without markdown
    if not code_blocks and 'def test_' in response_text:
        # Check if the text starts with imports that suggest Python code
        if any(pattern in response_text for pattern in ['import ', 'from ', 'def test_']):
            code_blocks = [response_text]
    
    # If only one large code block is found, try to split it into individual test functions
    if len(code_blocks) == 1 and code_blocks[0].count('def test_') > 1:
        # Extract individual test functions
        test_functions = []
        current_function = []
        in_function = False
        
        for line in code_blocks[0].split('\n'):
            # Skip imports and other non-test code at the beginning
            if not in_function and not line.strip().startswith('def test_') and not current_function:
                continue
                
            # Start of a new function
            if line.strip().startswith('def test_'):
                # Save the previous function if it exists
                if current_function:
                    test_functions.append('\n'.join(current_function))
                current_function = [line]
                in_function = True
            # Inside a function
            elif in_function:
                # End of function detection - another top-level statement or end of block
                if line.strip() and not line.startswith(' ') and not line.startswith('\t') and not line.startswith('#'):
                    # If it's not a function call to one of our test functions
                    if not any(line.strip() == f"{func}()" for func in re.findall(r'def (test_[\w_]+)\(', '\n'.join(current_function))):
                        # Save the previous function
                        test_functions.append('\n'.join(current_function))
                        current_function = []
                        in_function = False
                        # Don't include this line as it's not part of any function
                        continue
                current_function.append(line)
        
        # Add the last function if it exists
        if current_function:
            test_functions.append('\n'.join(current_function))
        
        return test_functions
    
    return code_blocks

# Function to parse test case descriptions
def extract_test_descriptions(response_text):
    test_descriptions = {}
    
    # Extract test case IDs and descriptions
    test_case_pattern = r'\*\*Test Case \d+: ([^*]+)\*\*\s*\n\s*- \*\*Test Case ID:\*\* ([A-Z0-9]+)'
    matches = re.findall(test_case_pattern, response_text)
    
    for name, test_id in matches:
        test_descriptions[test_id] = name.strip()
    
    return test_descriptions

# Extract test cases and descriptions
test_cases = extract_test_cases(response_content_for_testing_code)
test_descriptions = extract_test_descriptions(response_content_for_testing_code)

# Create a Python file with all the test cases
if test_cases:
    # Create imports and setup code
    test_file_content = """import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class StockReportWebsiteTests(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()
        self.url = "http://example-stock-report.com"
        
    def tearDown(self):
        self.driver.quit()
"""
    
    # Process each test case
    for code_block in test_cases:
        # Extract function name and body
        function_match = re.search(r'def (test_[\w_]+)\(', code_block)
        if not function_match:
            continue
            
        function_name = function_match.group(1)
        
        # Extract test case ID and name from comments
        test_id_match = re.search(r'# Test case ID and descriptive name[\s\S]*?test_case_id = "([A-Z0-9_]+)"[\s\S]*?test_case_name = "([^"]+)"', code_block)
        test_id = None
        test_name = None
        if test_id_match:
            test_id = test_id_match.group(1)
            test_name = test_id_match.group(2)
        else:
            # Try to find test ID from function name if not found in comments
            for tid, desc in test_descriptions.items():
                if desc.lower().replace(' ', '_') in function_name.lower():
                    test_id = tid
                    test_name = desc
                    break
        
        # Extract test objective
        test_objective_match = re.search(r'# Test objective[\s\S]*?test_objective = "([^"]+)"', code_block)
        test_objective = test_objective_match.group(1) if test_objective_match else None
        
        # Start building the test method
        test_method = [f"    def {function_name}(self):"]
        
        # Add docstring with test description if available
        if test_id and test_name and test_objective:
            test_method.append(f'        """Test {test_id}: {test_name}\n        {test_objective}\n        """')
        elif test_id and test_name:
            test_method.append(f'        """Test {test_id}: {test_name}"""')
        
        # Add the line to navigate to the website
        test_method.append('        self.driver.get(self.url)')
        
        # Process the function body
        in_body = False
        skip_next_lines = 0
        in_multiline = False
        multiline_indent = 0
        in_try_block = False
        in_except_block = False
        in_finally_block = False
        current_block_type = None
        for line in code_block.split('\n'):
            # Skip lines as needed (for multi-line statements we want to skip)
            if skip_next_lines > 0:
                skip_next_lines -= 1
                continue
                
            # Detect start of function body
            if line.startswith('def test_'):
                in_body = True
                continue
            elif not in_body:
                continue
                
            # Skip test case metadata comments and variable assignments
            if line.strip().startswith('# Test case ID') or \
               line.strip().startswith('test_case_id =') or \
               line.strip().startswith('test_case_name =') or \
               line.strip().startswith('# Test objective') or \
               line.strip().startswith('test_objective =') or \
               line.strip().startswith('# Preconditions') or \
               line.strip().startswith('preconditions ='):
                continue
                
            # Skip driver creation and navigation (but keep driver.quit() in finally blocks)
            if ('driver = webdriver.Chrome()' in line or 
                'driver.get(' in line or 
                'webdriver.Chrome()' in line or 
                line.strip() == 'driver = None') and not in_finally_block:
                continue
                
            # Skip print statements for test results unless they're in except blocks
            if line.strip().startswith('print(') and any(x in line for x in ['test_case_name', 'passed', 'failed', 'Starting']) and not in_except_block:
                continue
            
            # Track block types
            if line.strip() == 'try:':
                in_try_block = True
                in_except_block = False
                in_finally_block = False
                current_block_type = 'try'
            elif line.strip().startswith('except'):
                in_try_block = False
                in_except_block = True
                in_finally_block = False
                current_block_type = 'except'
            elif line.strip() == 'finally:':
                in_try_block = False
                in_except_block = False
                in_finally_block = True
                current_block_type = 'finally'
                
            # Skip empty lines and function calls
            if not line.strip() or line.strip() == function_name + '()':
                continue
                
            # Replace driver. with self.driver.
            line = line.replace('driver.', 'self.driver.')
            # Also replace WebDriverWait(driver with WebDriverWait(self.driver
            line = line.replace('WebDriverWait(driver', 'WebDriverWait(self.driver')
            
            # Update to new Selenium API
            line = line.replace('find_element_by_id(', 'find_element(By.ID, ')
            line = line.replace('find_element_by_name(', 'find_element(By.NAME, ')
            line = line.replace('find_element_by_class_name(', 'find_element(By.CLASS_NAME, ')
            line = line.replace('find_element_by_tag_name(', 'find_element(By.TAG_NAME, ')
            line = line.replace('find_element_by_xpath(', 'find_element(By.XPATH, ')
            line = line.replace('find_element_by_css_selector(', 'find_element(By.CSS_SELECTOR, ')
            
            # Convert assertions
            if line.strip().startswith('assert '):
                # Extract the assertion message if present
                message = ""
                if ',' in line and line.count('"') >= 2:
                    parts = line.split(',', 1)
                    line = parts[0]
                    message = parts[1].strip()
                    if message.startswith('"') and message.endswith('"'):
                        message = ", " + message
                    else:
                        message = ""
                
                if ' in ' in line and ' and ' not in line:
                    line = re.sub(r'assert (.*) in (.*)', r'self.assertIn(\1, \2' + message + ')', line)
                elif ' == ' in line and ' and ' not in line:
                    line = re.sub(r'assert (.*) == (.*)', r'self.assertEqual(\1, \2' + message + ')', line)
                elif ' and ' in line:
                    # Handle compound assertions with 'and'
                    line = line.replace('assert ', 'self.assertTrue(')
                    if message:
                        if line.strip().endswith(')'):
                            line = line.strip()[:-1] + message + ')'
                        else:
                            line = line.strip() + message + ')'
                    elif not line.strip().endswith(')'): 
                        line = line.strip() + ')'                
                else:
                    line = line.replace('assert ', 'self.assertTrue(')
                    if message:
                        if line.strip().endswith(')'):
                            line = line.strip()[:-1] + message + ')'
                        else:
                            line = line.strip() + message + ')'
                    elif not line.strip().endswith(')'):
                        line = line.strip() + ')'                
            
            # Track try/except blocks
            if line.strip().endswith('try:'):
                in_try_block = True
            elif line.strip().startswith('except') or line.strip().startswith('finally'):
                in_try_block = False
            
            # Check if this is part of a multi-line statement
            if '(' in line and ')' not in line and not line.strip().endswith(':'):
                in_multiline = True
                multiline_indent = len(line) - len(line.lstrip())
                
            # Handle assertions and actual_results for unittest
            if line.strip().startswith('assert '):
                # Convert assert statements to unittest assertions
                assertion = line.strip()[7:]
                if ' == ' in assertion:
                    parts = assertion.split(' == ')
                    left = parts[0].strip()
                    right = parts[1].strip()
                    
                    # Handle inline comments in assertions
                    comment = ""
                    if '#' in right:
                        right_parts = right.split('#', 1)
                        right = right_parts[0].strip()
                        comment = f"  # {right_parts[1].strip()}"
                    
                    # Handle rgba color values in assertions
                    if right.startswith("'rgba(") and not right.endswith("')"):
                        # Extract the message if there is one
                        message = ""
                        if '", "' in right:
                            right_parts = right.split('", "')
                            right = right_parts[0] + '"\''
                            message = ', "' + right_parts[1]
                        else:
                            # Complete the rgba string based on the value
                            if "'rgba(255" in right:
                                right = "'rgba(255, 255, 255, 1)'"
                            elif "'rgba(0" in right:
                                right = "'rgba(0, 0, 128, 1)'"
                    
                    test_method.append(f'            self.assertEqual({left}, {right}){comment}')
                else:
                    test_method.append(f'            self.assertTrue({assertion})')
                continue
                
            # Convert actual_results to assertions
            if line.strip().startswith('actual_results ='):
                # Extract the actual results and convert to assertion
                actual_results_match = re.search(r'actual_results = (.*)', line.strip())
                if actual_results_match:
                    actual_results_expr = actual_results_match.group(1)
                    # Save for later assertion
                    test_method.append(f'            self.assertTrue({actual_results_expr}, "Expected condition not met")')
                continue

            # Handle WebDriverWait statements - make sure they're inside try blocks
            if 'WebDriverWait' in line and not (in_try_block or in_except_block or in_finally_block):
                # If we find a WebDriverWait outside a try block, we need to add a try block
                test_method.append('        try:')
                in_try_block = True
                current_block_type = 'try'
                # Then add the WebDriverWait with proper indentation
                test_method.append('            ' + line.strip())
                # Track that we're in a multiline statement if needed
                if '(' in line and ')' not in line:
                    in_multiline = True
                    multiline_indent = len(line) - len(line.lstrip())
            # Handle try-except-finally blocks with proper indentation
            elif line.strip() == 'try:':
                test_method.append('        try:')
                in_try_block = True
                in_except_block = False
                in_finally_block = False
                current_block_type = 'try'
            elif line.strip().startswith('except'):
                test_method.append('        except ' + line.strip()[7:])
                in_try_block = False
                in_except_block = True
                in_finally_block = False
                current_block_type = 'except'
            elif line.strip() == 'finally:':
                test_method.append('        finally:')
                in_try_block = False
                in_except_block = False
                in_finally_block = True
                current_block_type = 'finally'
            # Handle indentation for multi-line statements
            elif in_multiline and line.strip() and not line.strip().endswith(':'):
                # If this line has more indentation than the start of the multi-line statement,
                # it's a continuation and needs to maintain its relative indentation
                if ')' in line and '(' not in line:
                    in_multiline = False  # End of multi-line statement
                
                # Add proper indentation based on current block type
                if current_block_type in ['try', 'except', 'finally']:
                    # Make sure multi-line WebDriverWait statements are properly indented
                    if 'EC.' in line:
                        test_method.append('                ' + line.strip())
                    else:
                        test_method.append('            ' + line.strip())
                else:
                    test_method.append('        ' + line.strip())
            else:
                # Regular line (not part of multi-line statement)
                # Add proper indentation based on current block type
                if current_block_type in ['try', 'except', 'finally']:
                    test_method.append('            ' + line.strip())
                else:
                    test_method.append('        ' + line.strip())
                    
                # Check if this is the start of a new multi-line statement
                if '(' in line and ')' not in line and not line.strip().endswith(':'):
                    in_multiline = True
                    multiline_indent = len(line) - len(line.lstrip())
        
        # Add the test method to the file content
        test_file_content += '\n' + '\n'.join(test_method) + '\n'
    
    # Add the main block to run the tests
    test_file_content += """

if __name__ == "__main__":
    unittest.main()
"""
    
    # Write the test file
    with open('stock_report_tests-wo-code-script.py', 'w') as f:
        f.write(test_file_content)
    
    print("\nTest cases have been extracted and saved to 'stock_report_tests-wo-code-script.py'")
    
    # Fix syntax errors in the generated file
    def fix_syntax_errors(file_path):
        """Fix common syntax errors in the generated test file."""
        import re
        
        print("\nChecking for syntax errors in the generated file...")
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Split into lines for processing
        lines = content.split('\n')
        fixed_lines = []
        
        # Track indentation state
        in_with_block = False
        with_block_indent = 0
        
        for i, line in enumerate(lines):
            # Fix missing imports
            if i == 0:
                if 'import os' not in content and 'os.path' in content:
                    fixed_lines.append('import os')
                if 'import time' not in content and 'time.sleep' in content:
                    fixed_lines.append('import time')
                
            # Fix incomplete string literals in assertEqual statements
            if 'self.assertEqual(' in line and line.count('"') % 2 == 1:
                # Find where the string starts
                start_idx = line.find('"')
                if start_idx != -1:
                    # Complete the string and add closing parenthesis if needed
                    line = line[:start_idx+1] + line[start_idx+1:].replace('"', '') + '")'
            
            # Fix any assertion with missing closing parenthesis
            for assertion in ['self.assertEqual(', 'self.assertTrue(', 'self.assertFalse(', 'self.assertIn(', 'self.assertNotIn(']:
                if assertion in line and line.count('(') > line.count(')') and '#' not in line:
                    line = line.rstrip() + ')'
                elif assertion in line and '#' in line and line.count('(') > line.count(')'):
                    parts = line.split('#', 1)
                    code_part = parts[0].strip()
                    comment_part = parts[1].strip()
                    
                    # Add missing closing parenthesis
                    if code_part.count('(') > code_part.count(')'):
                        code_part += ')'
                    
                    line = code_part + ' # ' + comment_part
            
            # Fix indentation issues in with blocks
            if 'with open(' in line:
                in_with_block = True
                with_block_indent = len(line) - len(line.lstrip())
            elif in_with_block and line.strip() and len(line) - len(line.lstrip()) <= with_block_indent:
                in_with_block = False
            
            # Fix indentation for lines inside with blocks
            if in_with_block and 'content =' in line and len(line) - len(line.lstrip()) <= with_block_indent:
                line = ' ' * (with_block_indent + 4) + line.lstrip()
            
            # Fix WebDriverWait indentation
            if 'EC.' in line and line.strip().startswith('EC.'):
                # This is likely a continuation of WebDriverWait
                line = ' ' * 12 + line.lstrip()
            
            fixed_lines.append(line)
        
        # Join the fixed lines and write back to the file
        fixed_content = '\n'.join(fixed_lines)
        with open(file_path, 'w') as f:
            f.write(fixed_content)
        
        print("✓ Fixed common syntax errors in the file")
    
    # Run the syntax error fixer
    fix_syntax_errors('stock_report_tests-wo-code-script.py')
