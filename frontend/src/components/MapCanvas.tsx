// src/components/MapCanvas.tsx
import { RefObject } from "react";
import { Printer } from "@/lib/api";

interface MapCanvasProps {
    mapUrl: string | null;
    mapContainerRef: RefObject<HTMLDivElement | null>;
    onMapClick: (e: React.MouseEvent<HTMLDivElement>) => void;
    onMapUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
    printers: Printer[];
    onSelectPrinter: (printer: Printer) => void;
    clickCoords: { x: number; y: number } | null;
}

export function MapCanvas({
                              mapUrl,
                              mapContainerRef,
                              onMapClick,
                              onMapUpload,
                              printers,
                              onSelectPrinter,
                              clickCoords
                          }: MapCanvasProps) {
    if (!mapUrl) {
        return (
            <div className="text-center p-12 border-2 border-dashed border-zinc-700 rounded-xl max-w-md">
                <p className="text-zinc-400 mb-4">План офиса в формате SVG еще не загружен на сервер.</p>
                <label className="bg-am ber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-md font-medium text-sm cursor-pointer transition-colors">
                    Загрузить первую карту
                    <input type="file" accept=".svg" onChange={onMapUpload} className="hidden" />
                </label>
            </div>
        );
    }

    return (
        <div
            ref={mapContainerRef}
            onClick={onMapClick}
            className="relative shadow-2xl bg-zinc-800 rounded-lg overflow-hidden border border-zinc-700 select-none cursor-crosshair"
            style={{ width: "100%", maxWidth: "1200px", aspectRatio: "16/9" }}
        >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
                src={mapUrl}
                alt="План офиса"
                className="w-full h-full object-contain pointer-events-none"
            />

            {printers.map((printer) => (
                <button
                    key={printer.id}
                    className="printer-marker absolute group transform -translate-x-1/2 -translate-y-1/2 p-2 focus:outline-none transition-transform hover:scale-125 z-10"
                    style={{ left: `${printer.x}%`, top: `${printer.y}%` }}
                    onClick={() => onSelectPrinter(printer)}
                >
                    <span className={`relative flex h-4 w-4 rounded-full border-2 border-zinc-900 ${printer.status === 'online' ? 'bg-emerald-500' : 'bg-rose-500'}`}>
                        {printer.status === 'online' && (
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        )}
                    </span>

                    <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 hidden group-hover:block bg-zinc-950 text-white text-[11px] px-2 py-0.5 rounded shadow border border-zinc-700 whitespace-nowrap z-20">
                        {printer.name || printer.ip}
                    </span>
                </button>
            ))}

            {clickCoords && (
                <div
                    className="absolute transform -translate-x-1/2 -translate-y-1/2 h-5 w-5 border-2 border-dashed border-amber-400 bg-amber-400/20 rounded-full animate-pulse"
                    style={{ left: `${clickCoords.x}%`, top: `${clickCoords.y}%` }}
                />
            )}
        </div>
    );
}