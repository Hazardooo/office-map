import { Printer } from "@/service/api";

interface PrinterMarkerProps {
    printer: Printer;
    isSelected: boolean;
    isMoving: boolean;
    isLinked: boolean;
    isLinkingMode: boolean;
    isFaded: boolean;
    onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
}

export function PrinterMarker({ printer, isSelected, isMoving, isLinked, isLinkingMode, isFaded, onClick }: PrinterMarkerProps) {
    // Вычисляем классы на основе статуса, используя семантические переменные CSS
    const getBaseColor = () => {
        if (isLinked) return "bg-brand border-surface-muted";
        if (isFaded) return "bg-status-disabled border-border";
        return printer.is_online ? "bg-status-online border-surface-muted" : "bg-status-offline border-surface-muted";
    };

    return (
        <button
            className={`
                absolute group transform -translate-x-1/2 -translate-y-1/2 p-2 focus:outline-none transition-all z-10 duration-500
                ${isMoving ? "scale-150 z-50 cursor-grabbing" : "hover:scale-125 cursor-pointer"}
                ${isSelected && !isMoving && !isLinkingMode ? "ring-2 ring-status-online rounded-full" : ""}
                ${isLinked ? "z-20 scale-125" : ""} 
                ${isFaded ? "opacity-60" : "opacity-100"} 
            `}
            style={{ left: `${printer.x}%`, top: `${printer.y}%` }}
            onClick={onClick}
        >
            {/* Сама точка (кружок) */}
            <span className={`relative flex h-4 w-4 rounded-full border-2 transition-colors duration-300 ${getBaseColor()} ${isMoving ? 'animate-bounce shadow-lg shadow-status-online/50' : ''}`}>
                {printer.is_online && !isMoving && !isFaded && !isLinkingMode && (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-online opacity-75"></span>
                )}
            </span>

            {/* Всплывающая подсказка */}
            <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-1 hidden group-hover:block bg-surface-muted text-text-main text-[11px] px-2 py-0.5 rounded shadow border border-border whitespace-nowrap z-30 pointer-events-none">
                {printer.name || printer.ip}
                {isMoving && " → клик на карту"}
                {isLinkingMode && !isLinked && " → клик чтобы связать"}
                {isLinkingMode && isLinked && " → клик чтобы отвязать"}
            </span>
        </button>
    );
}