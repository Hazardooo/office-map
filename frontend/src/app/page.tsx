"use client";

import { useOfficeMap } from "@/hooks/useOfficeMap";
import { Sidebar } from "@/components/Sidebar";
import { MapCanvas } from "@/components/MapCanvas";

export default function OfficeMapPage() {
    const {
        printers,
        totalPrinters,
        mapUrl,
        loading,
        clickCoords,
        newPrinter,
        selectedPrinter,
        mode,
        mapContainerRef,
        cartridges,
        selectedCartridgeId,
        hoveredCartridgeId,
        isLinking,
        linkingPrinterIds,
        setHoveredCartridgeId,
        setIsLinking,
        setLinkingPrinterIds,
        setSelectedCartridgeId,
        loadCartridges,
        setNewPrinter,
        setClickCoords,
        setSelectedPrinter,
        handleMapUpload,
        handleMapClick,
        handleCreatePrinter,
        handleRefresh,
        handleDelete,
        handleStartMove,
        handleCancelMove,
        handleRename,
        handleSelectPrinter
    } = useOfficeMap();

    return (
        <div className="flex h-screen bg-zinc-900 text-zinc-100 font-sans">
            <Sidebar
                loading={loading}
                totalPrinters={totalPrinters}
                mode={mode}
                onMapUpload={handleMapUpload}
                clickCoords={clickCoords}
                newPrinter={newPrinter}
                setNewPrinter={setNewPrinter}
                onCreatePrinter={handleCreatePrinter}
                setClickCoords={setClickCoords}
                selectedPrinter={selectedPrinter}
                onRefresh={handleRefresh}
                onDelete={handleDelete}
                onStartMove={handleStartMove}
                onCancelMove={handleCancelMove}
                onRename={handleRename}

                printers={printers}
                cartridges={cartridges}
                selectedCartridgeId={selectedCartridgeId}
                onSelectCartridge={setSelectedCartridgeId}
                onRefreshCartridges={loadCartridges}

                // Новые пропсы для hover и режима связывания
                setHoveredCartridgeId={setHoveredCartridgeId}
                isLinking={isLinking}
                setIsLinking={setIsLinking}
                linkingPrinterIds={linkingPrinterIds}
                setLinkingPrinterIds={setLinkingPrinterIds}
            />

            <main className="flex-1 flex flex-col items-center justify-center p-8 bg-zinc-900 overflow-auto relative">
                <MapCanvas
                    mapUrl={mapUrl}
                    mode={mode}
                    selectedPrinter={selectedPrinter}
                    mapContainerRef={mapContainerRef}
                    onMapClick={handleMapClick}
                    onMapUpload={handleMapUpload}
                    printers={printers}
                    onSelectPrinter={handleSelectPrinter}
                    clickCoords={clickCoords}

                    cartridges={cartridges}
                    selectedCartridgeId={selectedCartridgeId}
                    hoveredCartridgeId={hoveredCartridgeId}
                    isLinking={isLinking}
                    linkingPrinterIds={linkingPrinterIds}
                />
            </main>
        </div>
    );
}