"use client";

import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';

// Component for rendering the animated SVG chart
const EquityChart = ({ data, benchmarkData }: { data: any[], benchmarkData: any[] }) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const { pathData, benchmarkPathData, points, minY, maxY } = useMemo(() => {
    if (!data || data.length === 0) return { pathData: "", benchmarkPathData: "", points: [], minY: 0, maxY: 0 };
    
    // Determine min and max Y for scaling
    let currentMin = Math.min(data[0].value, benchmarkData[0].value);
    let currentMax = Math.max(data[0].value, benchmarkData[0].value);
    
    for (let i = 0; i < data.length; i++) {
      if (data[i].value < currentMin) currentMin = data[i].value;
      if (data[i].value > currentMax) currentMax = data[i].value;
      if (benchmarkData[i] && benchmarkData[i].value < currentMin) currentMin = benchmarkData[i].value;
      if (benchmarkData[i] && benchmarkData[i].value > currentMax) currentMax = benchmarkData[i].value;
    }
    
    // Add some padding
    const range = currentMax - currentMin;
    currentMin = Math.max(0, currentMin - range * 0.1);
    currentMax = currentMax + range * 0.1;
    
    // Scale points to 1000x300 viewBox
    const width = 1000;
    const height = 300;
    
    const mappedPoints = data.map((d, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((d.value - currentMin) / (currentMax - currentMin)) * height;
      return { x, y, date: d.date, value: d.value };
    });
    
    const mappedBenchmark = benchmarkData.map((d, i) => {
      const x = (i / (benchmarkData.length - 1)) * width;
      const y = height - ((d.value - currentMin) / (currentMax - currentMin)) * height;
      return { x, y };
    });
    
    const pathStr = `M ${mappedPoints.map(p => `${p.x},${p.y}`).join(" L ")}`;
    const benchPathStr = `M ${mappedBenchmark.map(p => `${p.x},${p.y}`).join(" L ")}`;
    
    return { pathData: pathStr, benchmarkPathData: benchPathStr, points: mappedPoints, minY: currentMin, maxY: currentMax };
  }, [data, benchmarkData]);

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    const index = Math.floor(percentage * (points.length - 1));
    setHoverIndex(index);
  };

  if (!pathData) return null;

  return (
    <div className="relative w-full h-[300px] border border-line bg-ink group">
      <svg 
        viewBox="0 0 1000 300" 
        preserveAspectRatio="none" 
        className="w-full h-full"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverIndex(null)}
      >
        {/* Grid lines */}
        <line x1="0" y1="75" x2="1000" y2="75" stroke="var(--color-line)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="150" x2="1000" y2="150" stroke="var(--color-line)" strokeWidth="1" strokeDasharray="4 4" />
        <line x1="0" y1="225" x2="1000" y2="225" stroke="var(--color-line)" strokeWidth="1" strokeDasharray="4 4" />
        
        {/* Benchmark Path (quiet) */}
        <path 
          d={benchmarkPathData} 
          fill="none" 
          stroke="var(--color-line)" 
          strokeWidth="1.5" 
          opacity={0.8}
        />
        
        {/* Strategy Path (animated draw-on) */}
        <motion.path
          d={pathData}
          fill="none"
          stroke="var(--color-signal-up)"
          strokeWidth="2"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />

        {/* Interactive Cursor */}
        {hoverIndex !== null && points[hoverIndex] && (
          <g>
            <line 
              x1={points[hoverIndex].x} 
              y1="0" 
              x2={points[hoverIndex].x} 
              y2="300" 
              stroke="var(--color-accent)" 
              strokeWidth="1" 
              opacity={0.5} 
            />
            <circle 
              cx={points[hoverIndex].x} 
              cy={points[hoverIndex].y} 
              r="4" 
              fill="var(--color-ink)" 
              stroke="var(--color-accent)" 
              strokeWidth="2" 
            />
          </g>
        )}
      </svg>
      
      {/* Floating Readout */}
      {hoverIndex !== null && points[hoverIndex] && (
        <div 
          className="absolute top-4 left-4 bg-ink border border-line px-3 py-2 text-xs font-mono z-10 pointer-events-none"
        >
          <div className="text-gray-400 mb-1">{points[hoverIndex].date}</div>
          <div className="text-paper">Strategy: {(points[hoverIndex].value * 100 - 100).toFixed(2)}%</div>
          <div className="text-gray-500">Benchmark: {(benchmarkData[hoverIndex].value * 100 - 100).toFixed(2)}%</div>
        </div>
      )}
    </div>
  );
};

export default function DashboardClient({ data }: { data: any }) {
  const strategies = Object.keys(data.strategies);
  const [selectedStrategy, setSelectedStrategy] = useState(strategies[0]);

  const activeData = data.strategies[selectedStrategy];
  const activeMetrics = activeData.metrics.net;
  const benchmarkMetrics = data.benchmark.metrics;

  const formatPct = (val: number) => `${(val * 100).toFixed(2)}%`;
  const formatDec = (val: number) => val.toFixed(2);

  return (
    <div className="max-w-6xl mx-auto p-8 pt-12">
      <header className="mb-8 border-b border-line pb-6 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="font-display text-2xl text-paper tracking-tight mb-2">Backtest Ledger</h1>
          <p className="text-gray-400 text-sm font-sans">Quantitative strategy simulation engine &middot; 20 liquid equities</p>
        </div>
        
        {/* Strategy Selector */}
        <div className="flex border border-line p-1 bg-ink">
          {strategies.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedStrategy(s)}
              className={`px-4 py-1.5 text-xs font-mono relative z-10 transition-colors ${
                selectedStrategy === s ? 'text-ink' : 'text-gray-400 hover:text-paper'
              }`}
            >
              {selectedStrategy === s && (
                <motion.div
                  layoutId="strategyTab"
                  className="absolute inset-0 bg-accent z-[-1]"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </header>

      {/* Main Chart */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-sm tracking-widest uppercase text-gray-500">Equity Curve</h2>
          <div className="flex gap-4 text-xs font-mono text-gray-500">
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 bg-signal-up"></div> Strategy</span>
            <span className="flex items-center gap-1.5"><div className="w-2 h-2 border border-line bg-ink"></div> Benchmark</span>
          </div>
        </div>
        <EquityChart data={activeData.equity_curve} benchmarkData={data.benchmark.equity_curve} />
      </section>

      {/* Metrics Table */}
      <section>
        <h2 className="font-display text-sm tracking-widest uppercase text-gray-500 mb-3">Performance Metrics (Net of 5bps)</h2>
        <div className="w-full overflow-x-auto border border-line">
          <table className="w-full text-sm font-mono text-right border-collapse">
            <thead>
              <tr className="border-b border-line text-gray-400 bg-[#0F131A]">
                <th className="py-3 px-4 text-left font-normal border-r border-line">Metric</th>
                <th className="py-3 px-4 font-normal border-r border-line">Strategy</th>
                <th className="py-3 px-4 font-normal border-r border-line">Benchmark</th>
                <th className="py-3 px-4 font-normal">Variance</th>
              </tr>
            </thead>
            <tbody>
              {[
                { label: 'Total Return', key: 'Total Return', fmt: formatPct },
                { label: 'CAGR', key: 'CAGR', fmt: formatPct },
                { label: 'Sharpe Ratio', key: 'Sharpe Ratio', fmt: formatDec },
                { label: 'Max Drawdown', key: 'Max Drawdown', fmt: formatPct },
                { label: 'Annualized Volatility', key: 'Annualized Volatility', fmt: formatPct },
                { label: 'Win Rate', key: 'Win Rate', fmt: formatPct },
              ].map((row, idx) => {
                const stratVal = activeMetrics[row.key] || 0;
                const benchVal = benchmarkMetrics[row.key] || 0;
                const variance = stratVal - benchVal;
                
                // For Drawdown and Volatility, lower is better. For others, higher is better.
                const isInverse = row.key === 'Max Drawdown' || row.key === 'Annualized Volatility';
                const isPositive = isInverse ? variance < 0 : variance > 0;
                
                return (
                  <tr key={row.key} className="border-b border-line last:border-0 hover:bg-[#0F131A] transition-colors">
                    <td className="py-3 px-4 text-left border-r border-line text-gray-300">{row.label}</td>
                    <td className="py-3 px-4 border-r border-line text-paper">{row.fmt(stratVal)}</td>
                    <td className="py-3 px-4 border-r border-line text-gray-500">{row.fmt(benchVal)}</td>
                    <td className={`py-3 px-4 ${isPositive ? 'text-signal-up' : 'text-signal-down'}`}>
                      {variance > 0 ? '+' : ''}{row.fmt(variance)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
