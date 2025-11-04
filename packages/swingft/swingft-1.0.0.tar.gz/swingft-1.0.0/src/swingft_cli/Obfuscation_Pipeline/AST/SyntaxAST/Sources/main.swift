// The Swift Programming Language
// https://docs.swift.org/swift-book

import Foundation

let sourceListPath = CommandLine.arguments[1]
let externalSourceListPath = CommandLine.arguments[2]
let outputPath = CommandLine.arguments[3]

let internalH = InternalHandler(sourceListPath: sourceListPath, outputPath: outputPath)
try internalH.readAndProcess()
let externalH = ExternalHandler(sourceListPath: externalSourceListPath, outputPath: outputPath)
try externalH.readAndProcess()
