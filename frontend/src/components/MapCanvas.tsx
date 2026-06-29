import { RefObject } from "react";
import { Printer, Cartridge } from "@/service/api";
import { PrinterMarker } from "./PrinterMarker";

interface MapCanvasProps {
    mapUrl: string | null;
    mode: "view" | "add" | "move";
    selectedPrinter: Printer | null;
    mapContainerRef: RefObject<HTMLDivElement | null>;
    onMapClick: (e: React.MouseEvent<HTMLDivElement>) => void;
    onMapUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
    printers: Printer[];
    onSelectPrinter: (printer: Printer) => void;
    clickCoords: { x: number; y: number } | null;
    cartridges: Cartridge[];
    selectedCartridgeId: string | null;
    hoveredCartridgeId: string | null;
    isLinking: boolean;
    linkingPrinterIds: string[];
}

export function MapCanvas({
                              mapUrl, mode, selectedPrinter, mapContainerRef, onMapClick, onMapUpload, printers,
                              onSelectPrinter, clickCoords, cartridges, selectedCartridgeId, hoveredCartridgeId,
                              isLinking, linkingPrinterIds
                          }: MapCanvasProps) {
    if (!mapUrl) {
        return (
            <div className="text-center p-12 border-2 border-dashed border-border rounded-xl max-w-md">
                <p className="text-text-muted mb-4">План офиса в формате SVG еще не загружен на сервер.</p>
                <label className="bg-brand-dark hover:bg-brand text-white px-4 py-2 rounded-md font-medium text-sm cursor-pointer transition-colors">
                    Загрузить первую карту
                    <input type="file" accept=".svg" onChange={onMapUpload} className="hidden" />
                </label>
            </div>
        );
    }

    const isMoveMode = mode === "move";
    const activeCartridgeId = hoveredCartridgeId || selectedCartridgeId;
    const activeCartridge = cartridges.find(c => c.id === activeCartridgeId);
    const highlightedPrinterIds = activeCartridge ? new Set(activeCartridge.printer_ids || []) : null;

    return (
        <div className="relative w-full h-full flex flex-col items-center">
            {isMoveMode && selectedPrinter && (
                <div className="flex-shrink-0 z-30 mb-3 bg-brand-dark text-white text-sm font-medium px-5 py-2 rounded-full shadow-lg animate-pulse">
                    Кликните на карту, чтобы переместить «{selectedPrinter.name || selectedPrinter.ip}»
                </div>
            )}
            {isLinking && (
                <div className="flex-shrink-0 z-30 mb-3 bg-brand text-surface-muted text-sm font-bold px-5 py-2 rounded-full shadow-lg shadow-brand/20 animate-pulse">
                    Режим связывания: кликайте по принтерам на карте
                </div>
            )}

            <div
                ref={mapContainerRef}
                onClick={onMapClick}
                className={`
                    relative shadow-2xl rounded-lg overflow-hidden border select-none transition-all duration-200
                    ${isMoveMode ? "cursor-move border-brand/50 ring-2 ring-brand/20" : isLinking ? "border-brand shadow-brand/10 cursor-crosshair" : "cursor-pointer border-border"}
                `}
                style={{ width: "100%", maxWidth: "1400px", aspectRatio: "16/9" }}
            >
                <img src={mapUrl} alt="План офиса" className="w-full h-full object-contain pointer-events-none bg-surface-muted" />

                {printers.map((printer) => {
                    const isLinked = isLinking && linkingPrinterIds.includes(printer.id);
                    const isFadedByHover = !isLinking && highlightedPrinterIds && !highlightedPrinterIds.has(printer.id);
                    const isUnlinkedWhileLinking = isLinking && !isLinked;

                    return (
                        <PrinterMarker
                            key={printer.id}
                            printer={printer}
                            isSelected={selectedPrinter?.id === printer.id}
                            isMoving={isMoveMode && selectedPrinter?.id === printer.id}
                            isLinked={isLinked}
                            isLinkingMode={isLinking}
                            isFaded={Boolean(isFadedByHover || isUnlinkedWhileLinking)}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (!isMoveMode) onSelectPrinter(printer);
                            }}
                        />
                    );
                })}

                {clickCoords && mode === "add" && !isLinking && (
                    <div className="absolute transform -translate-x-1/2 -translate-y-1/2 h-5 w-5 border-2 border-dashed border-brand bg-brand-muted rounded-full animate-pulse z-20"
                         style={{ left: `${clickCoords.x}%`, top: `${clickCoords.y}%` }} />
                )}
            </div>
        </div>
    );
}