import React, { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import axios from 'axios'

export const Route = createFileRoute('/')({
  component: App,
})

const directionMap = {
  up: '↑',
  down: '↓',
  left: '←',
  right: '→',
}

function App() {
  const [layout, setLayout] = useState<Array<Array<number>>>([])
  const [shelves, setShelves] = useState<Record<string, Array<number>>>({})
  const [pickList, setPickList] = useState('')
  const [path, setPath] = useState<Array<Array<number>>>([])
  const [routePoints, setRoutePoints] = useState<Array<Record<string, any>>>([])
  const [directions, setDirections] = useState<
    Record<string, Array<string> | undefined>
  >({})

  useEffect(() => {
    axios.get('http://localhost:5000/api/layout').then((res) => {
      setLayout(res.data.layout)
      setShelves(res.data.shelves)
    })
  }, [])

  const handleSolve = async () => {
    const skus = pickList.split(/\s|,/).filter(Boolean)
    const res = await axios.post('http://localhost:5000/api/visualize-route', {
      pick_list: skus,
    })
    setLayout(res.data.visual_grid)
    setRoutePoints(res.data.route_points)
    setDirections(res.data.directions)
    setPath(res.data.path)
  }
  function displayContent(x: number, y: number) {
    let content = routePoints
      .map((point) =>
        point.position[0] === y && point.position[1] === x
          ? '' + point.order
          : '',
      )
      .filter(Boolean)
      .join(', ')
    if (content.length === 0) {
      const direction = directions[`${y},${x}`]
      if (direction && direction.length > 0) {
        content = direction.map((val) => <span>{directionMap[val]}</span>)
      }
    }
    return content
  }

  const renderGrid = () => {
    const cellSize = 50
    return layout.map((row, y) => (
      <div key={y} style={{ display: 'flex' }}>
        {row.map((cell, x) => {
          const isShelf = Object.values(shelves).some(
            ([sy, sx]) => sx === x && sy === y,
          )
          const isPath = path.some(([py, px]) => px === x && py === y)
          let bgColor = "#fff"
          let textColor = "#1c1b1f"
          if (cell >= 3){
            bgColor = "#0b5"
          } else if (isPath) {
            bgColor = '#005'
            textColor = '#fff'
          } else if (cell === 1){
            bgColor = "#999"
          } else if (isShelf){
            bgColor = '#f80'
          }
          return (
            <div
              className="flex items-center justify-center text-xs relative"
              key={x}
              style={{
                width: cellSize,
                height: cellSize,
                border: '1px solid #ccc',
                backgroundColor:bgColor,
                color: textColor
              }}
            >
              <span className="absolute top-0 left-0">
                {isShelf
                  ? Object.keys(shelves).filter(
                      (key) => shelves[key][0] === y && shelves[key][1] === x,
                    )
                  : ''}
              </span>
              <span className="text-white">{displayContent(x, y)}</span>
            </div>
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
