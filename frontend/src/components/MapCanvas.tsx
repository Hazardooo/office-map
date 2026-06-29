import {RefObject} from "react";
import {Printer, Cartridge} from "@/service/api";

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
                              mapUrl,
                              mode,
                              selectedPrinter,
                              mapContainerRef,
                              onMapClick,
                              onMapUpload,
                              printers,
                              onSelectPrinter,
                              clickCoords,
                              cartridges,
                              selectedCartridgeId,
                              hoveredCartridgeId,
                              isLinking,
                              linkingPrinterIds
                          }: MapCanvasProps) {
    if (!mapUrl) {
        return (
            <div className="text-center p-12 border-2 border-dashed border-zinc-700 rounded-xl max-w-md">
                <p className="text-zinc-400 mb-4">План офиса в формате SVG еще не загружен на сервер.</p>
                <label
                    className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-md font-medium text-sm cursor-pointer transition-colors">
                    Загрузить первую карту
                    <input type="file" accept=".svg" onChange={onMapUpload} className="hidden"/>
                </label>
            </div>
        );
    }

    const isMoveMode = mode === "move";
    const isAddMode = mode === "add";

    // Логика подсветки связанных принтеров при клике или наведении на картридж
    const activeCartridgeId = hoveredCartridgeId || selectedCartridgeId;
    const activeCartridge = cartridges.find(c => c.id === activeCartridgeId);
    const highlightedPrinterIds = activeCartridge ? new Set(activeCartridge.printer_ids || []) : null;

    return (
        <div className="relative w-full h-full flex flex-col items-center">
            {isMoveMode && selectedPrinter && (
                <div className="flex-shrink-0 z-30 mb-3">
                    <div
                        className="bg-amber-600 text-white text-sm font-medium px-5 py-2 rounded-full shadow-lg animate-pulse">
                        Кликните на карту, чтобы переместить «{selectedPrinter.name || selectedPrinter.ip}»
                    </div>
                </div>
            )}
            {isLinking && (
                <div className="flex-shrink-0 z-30 mb-3">
                    <div
                        className="bg-amber-500 text-zinc-950 text-sm font-bold px-5 py-2 rounded-full shadow-lg shadow-amber-500/20 animate-pulse">
                        Режим связывания: кликайте по принтерам на карте
                    </div>
                </div>
            )}

            <div
                ref={mapContainerRef}
                onClick={onMapClick}
                className={`
                    relative shadow-2xl rounded-lg overflow-hidden border select-none
                    transition-all duration-200
                    ${isMoveMode
                    ? " border-amber-500/50 ring-2 ring-amber-500/20"
                    : isLinking
                        ? "border-amber-500 shadow-amber-500/10 cursor-crosshair"
                        : isAddMode
                            ? "cursor-pointer border-zinc-700"
                            : "cursor-default border-zinc-700"
                }
                `}
                style={{width: "100%", maxWidth: "1400px", aspectRatio: "16/9"}}
            >
                {isMoveMode && (
                    <div
                        className="absolute inset-0 pointer-events-none opacity-10"
                        style={{
                            backgroundImage: `
                                linear-gradient(to right, #f59e0b 1px, transparent 1px),
                                linear-gradient(to bottom, #f59e0b 1px, transparent 1px)
                            `,
                            backgroundSize: '20px 20px'
                        }}
                    />
                )}

                <img
                    src={mapUrl}
                    alt="План офиса"
                    className="w-full h-full object-contain pointer-events-none"
                />

                {printers.map((printer) => {
                    const isSelected = selectedPrinter?.id === printer.id;
                    const isMoving = isMoveMode && isSelected;

                    const isLinked = isLinking && linkingPrinterIds.includes(printer.id);
                    const isFadedByHover = !isLinking && highlightedPrinterIds && !highlightedPrinterIds.has(printer.id);
                    const isUnlinkedWhileLinking = isLinking && !isLinked;

                    return (
                        <button
                            key={printer.id}
                            data-printer-id={printer.id}
                            className={`
                                printer-marker absolute group transform -translate-x-1/2 -translate-y-1/2 p-2 focus:outline-none transition-all z-10 duration-500
                                ${isMoving ? "scale-150 z-50 " : "hover:scale-125 cursor-pointer"}
                                ${isSelected && !isMoving && !isLinking ? "ring-2 ring-green-500 rounded-full" : ""}
                                ${isLinked ? "z-20 scale-125" : ""} 
                                ${isFadedByHover || isUnlinkedWhileLinking ? "opacity-60" : "opacity-100"} 
                            `}
                            style={{left: `${printer.x}%`, top: `${printer.y}%`}}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (!isMoveMode) {
                                    onSelectPrinter(printer);
                                }
                            }}
                        >
                            <span className={`
                                relative flex h-4 w-4 rounded-full border-2 transition-colors duration-300
                                ${isLinked
                                ? 'bg-amber-600 border-zinc-900'
                                : (isUnlinkedWhileLinking || isFadedByHover)
                                    ? 'bg-zinc-50 border-zinc-50'
                                    : printer.is_online
                                        ? 'bg-green-500 border-zinc-900'
                                        : 'bg-rose-500 border-zinc-900'
                            }
                                ${isMoving ? 'animate-bounce shadow-lg shadow-green-500/50' : ''}
                            `}>
                                {printer.is_online && !isMoving && !isFadedByHover && !isLinking && (
                                    <span
                                        className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                )}
                            </span>

                            <span
                                className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 hidden group-hover:block bg-zinc-950 text-white text-[11px] px-2 py-0.5 rounded shadow border border-zinc-700 whitespace-nowrap z-30">
                                {printer.name || printer.ip}
                                {isMoving && " → клик на карту"}
                                {isLinking && !isLinked && " → клик чтобы связать"}
                                {isLinking && isLinked && " → клик чтобы отвязать"}
                            </span>
                        </button>
                    );
                })}

                {clickCoords && isAddMode && !isLinking && (
                    <div
                        className="absolute transform -translate-x-1/2 -translate-y-1/2 h-5 w-5 border-2 border-dashed border-amber-400 bg-amber-400/20 rounded-full animate-pulse z-20"
                        style={{left: `${clickCoords.x}%`, top: `${clickCoords.y}%`}}
                    />
                )}
            </div>
        </div>
    );
}