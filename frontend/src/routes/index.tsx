import React, { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import axios from 'axios'

export const Route = createFileRoute('/')({
  component: App,
})

function App() {
  const [layout, setLayout] = useState<Array<Array<number>>>([])
  const [shelves, setShelves] = useState<Record<string, Array<number>>>({})
  const [pickList, setPickList] = useState('')
  const [path, setPath] = useState<Array<Array<number>>>([])

  useEffect(() => {
    axios.get('http://localhost:5000/api/layout').then((res) => {
      setLayout(res.data.layout)
      setShelves(res.data.shelves)
    })
  }, [])

  const handleSolve = async () => {
    const skus = pickList.split(/\s|,/).filter(Boolean)
    const res = await axios.post('http://localhost:5000/api/solve', {
      pick_list: skus,
    })
    setPath(res.data.path)
  }

  const renderGrid = () => {
    const cellSize = 25
    return layout.map((row, y) => (
      <div key={y} style={{ display: 'flex' }}>
        {row.map((cell, x) => {
          const isShelf = Object.values(shelves).some(
            ([sx, sy]) => sx === x && sy === y,
          )
          const isPath = path.some(([px, py]) => px === x && py === y)
          return (
            <div
              key={x}
              style={{
                width: cellSize,
                height: cellSize,
                border: '1px solid #ccc',
                backgroundColor: isPath
                  ? 'limegreen'
                  : isShelf
                    ? 'orange'
                    : cell === 1
                      ? '#999'
                      : '#fff',
              }}
            />
          )
        })}
      </div>
    ))
  }
  return (
    <div className="p-4 space-y-2 h-screen flex flex-col">
      <h1 className="text-xl font-bold">Warehouse Pick Optimizer</h1>
      <textarea
        value={pickList}
        onChange={(e) => setPickList(e.target.value)}
        placeholder="Enter SKUs (comma or space-separated)"
        className="w-full p-2 border"
        rows={3}
      />
      <button
        onClick={handleSolve}
        className="px-4 py-2 bg-blue-600 text-white rounded w-fit"
      >
        Optimize Path
      </button>
      <div className="overflow-auto h-full">{renderGrid()}</div>
    </div>
  )
}
