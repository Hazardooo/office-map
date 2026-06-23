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
        mapContainerRef,
        setNewPrinter,
        setClickCoords,
        setSelectedPrinter,
        handleMapUpload,
        handleMapClick,
        handleCreatePrinter,
        handleRefresh,
        handleDelete,
    } = useOfficeMap();

    return (
        <div className="flex h-screen bg-zinc-900 text-zinc-100 font-sans">
            <Sidebar
                loading={loading}
                totalPrinters={totalPrinters}
                onMapUpload={handleMapUpload}
                clickCoords={clickCoords}
                newPrinter={newPrinter}
                setNewPrinter={setNewPrinter}
                onCreatePrinter={handleCreatePrinter}
                setClickCoords={setClickCoords}
                selectedPrinter={selectedPrinter}
                onRefresh={handleRefresh}
                onDelete={handleDelete}
            />

            <main className="flex-1 flex flex-col items-center justify-center p-8 bg-zinc-900 overflow-auto relative">
                <MapCanvas
                    mapUrl={mapUrl}
                    mapContainerRef={mapContainerRef}
                    onMapClick={handleMapClick}
                    onMapUpload={handleMapUpload}
                    printers={printers}
                    onSelectPrinter={setSelectedPrinter}
                    clickCoords={clickCoords}
                />
            </main>
        </div>
    );
}