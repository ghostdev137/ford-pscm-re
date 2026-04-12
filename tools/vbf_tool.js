#!/usr/bin/env node
// VBF Tool - Decompress, modify, and rebuild Ford VBF files
// For ThyssenKrupp EPAS calibration files (data_format_identifier = 0x10)
// LZSS parameters from qvbf: EI=10, EJ=4, P=1, N=1024

const fs = require('fs');
const path = require('path');

const EI = 10, EJ = 4, P = 1, N = 1 << EI, F = (1 << EJ) + P;

// ---- LZSS Decompression ----
function lzssDecode(compressed) {
    const buffer = Buffer.alloc(N * 2, 0x20);
    let dataIdx = 0, buf = 0, mask = 0;
    const output = [];
    function getbit(n) {
        let x = 0;
        for (let i = 0; i < n; i++) {
            if (mask === 0) { if (dataIdx >= compressed.length) return -1; buf = compressed[dataIdx++]; mask = 128; }
            x <<= 1; if (buf & mask) x++; mask >>= 1;
        }
        return x;
    }
    let r = 0;
    while (true) {
        const c = getbit(1); if (c === -1) break;
        if (c) { const ch = getbit(8); if (ch === -1) break; output.push(ch); buffer[r++] = ch; r &= (N - 1); }
        else { const i = getbit(EI); if (i === -1) break; const j = getbit(EJ); if (j === -1) break; if (i === 0) break; const pos = i - 1; for (let k = 0; k <= j + 1; k++) { const ch = buffer[(pos + k) & (N - 1)]; output.push(ch); buffer[r++] = ch; r &= (N - 1); } }
    }
    return Buffer.from(output);
}

// ---- LZSS Compression (exact port of qvbf encode) ----
function lzssEncode(data) {
    const buffer = Buffer.alloc(N * 2, 0);
    let bitBuffer = 0, bitMask = 128;
    const output = [];

    function putbit1() {
        bitBuffer |= bitMask;
        bitMask >>= 1;
        if (bitMask === 0) { output.push(bitBuffer); bitBuffer = 0; bitMask = 128; }
    }
    function putbit0() {
        bitMask >>= 1;
        if (bitMask === 0) { output.push(bitBuffer); bitBuffer = 0; bitMask = 128; }
    }
    function output1(c) {
        putbit1();
        let mask = 256;
        while (mask >>= 1) { if (c & mask) putbit1(); else putbit0(); }
    }
    function output2(x, y) {
        putbit0();
        let mask = N;
        while (mask >>= 1) { if (x & mask) putbit1(); else putbit0(); }
        mask = (1 << EJ);
        while (mask >>= 1) { if (y & mask) putbit1(); else putbit0(); }
    }

    let dataIdx = 0;
    for (let i = N - F; i < N * 2; i++) {
        if (dataIdx >= data.length) break;
        buffer[i] = data[dataIdx++];
    }
    let bufferend = N - F + Math.min(data.length, N + F);
    if (bufferend > N * 2) bufferend = N * 2;
    // Recalculate bufferend properly
    bufferend = N - F;
    dataIdx = 0;
    for (let i = N - F; i < N * 2; i++) {
        if (dataIdx >= data.length) break;
        buffer[i] = data[dataIdx++];
        bufferend = i + 1;
    }

    let r = N - F;
    let s = 0;

    while (r < bufferend) {
        const f1 = (F <= bufferend - r) ? F : bufferend - r;
        let x = 0, y = 1;
        const c = buffer[r];

        for (let i = r - 1; i > s; i--) {
            if ((s >= (r - i)) && buffer[i] === c) {
                let j;
                for (j = 1; j < f1; j++) {
                    if (buffer[i + j] !== buffer[r + j]) break;
                }
                if (j > y) { x = i; y = j; }
            }
        }

        if (x >= (N - F)) x -= (N - F);
        x++;

        if (y <= P) {
            output1(c);
        } else {
            output2(x & (N - 1), y - 2);
        }

        r += y;
        s += y;

        if (r >= N * 2 - F) {
            for (let i = 0; i < N; i++) buffer[i] = buffer[i + N];
            bufferend -= N;
            r -= N;
            s -= N;
            while (bufferend < N * 2) {
                if (dataIdx >= data.length) break;
                buffer[bufferend++] = data[dataIdx++];
            }
        }
    }

    if (bitMask !== 128) output.push(bitBuffer);
    return Buffer.from(output);
}

// ---- CRC32 (polynomial 0x04C11DB7) ----
function crc32(data) {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < data.length; i++) {
        crc ^= (data[i] << 24);
        for (let j = 0; j < 8; j++) {
            if (crc & 0x80000000) crc = ((crc << 1) ^ 0x04C11DB7) >>> 0;
            else crc = (crc << 1) >>> 0;
        }
    }
    return crc >>> 0;
}

// ---- VBF Parser ----
function parseVBF(filepath) {
    const raw = fs.readFileSync(filepath);
    let depth = 0, inHeader = false, headerEnd = 0;
    for (let i = 0; i < raw.length; i++) {
        if (!inHeader && raw.slice(i, i + 6).toString() === 'header') inHeader = true;
        if (inHeader) {
            if (raw[i] === 0x7B) depth++;
            else if (raw[i] === 0x7D) { depth--; if (depth === 0) { headerEnd = i + 1; break; } }
        }
    }
    const headerText = raw.slice(0, headerEnd).toString('ascii');
    const addr = raw.readUInt32BE(headerEnd);
    const len = raw.readUInt32BE(headerEnd + 4);
    const payload = raw.slice(headerEnd + 8, headerEnd + 8 + len);

    const dfi = headerText.match(/data_format_identifier\s*=\s*(0x[0-9a-fA-F]+)/);
    const compressed = dfi && parseInt(dfi[1], 16) >> 4 !== 0;

    return { headerText, headerEnd, addr, len, payload, compressed, raw };
}

// ---- VBF Rebuilder ----
function rebuildVBF(original, newData) {
    const vbf = parseVBF(original);

    // Compress if original was compressed
    let blockData;
    if (vbf.compressed) {
        console.log('  Compressing with LZSS...');
        blockData = lzssEncode(newData);
        console.log(`  Compressed: ${newData.length} -> ${blockData.length} bytes`);
    } else {
        blockData = newData;
    }

    // Build block: addr(4) + length(4) + data(N) + crc16(2) - but VBF uses file_checksum CRC32
    // Actually the block has no per-block CRC for data_format=0x10
    const blockLen = blockData.length;

    // Calculate new file_checksum (CRC32 of all block data including addr, length, and data)
    const checksumData = Buffer.alloc(8 + blockLen);
    checksumData.writeUInt32BE(vbf.addr, 0);
    checksumData.writeUInt32BE(blockLen, 4);
    blockData.copy(checksumData, 8);
    const newChecksum = crc32(checksumData);

    // Update header with new checksum
    let newHeader = vbf.headerText.replace(
        /file_checksum\s*=\s*0x[0-9a-fA-F]+/,
        `file_checksum =  0x${newChecksum.toString(16).toUpperCase().padStart(8, '0')}`
    );

    // Build output file
    const headerBuf = Buffer.from(newHeader, 'ascii');
    const output = Buffer.alloc(headerBuf.length + 8 + blockLen);
    headerBuf.copy(output, 0);
    output.writeUInt32BE(vbf.addr, headerBuf.length);
    output.writeUInt32BE(blockLen, headerBuf.length + 4);
    blockData.copy(output, headerBuf.length + 8);

    return output;
}

// ---- CLI ----
const args = process.argv.slice(2);
const cmd = args[0];

if (cmd === 'decompress' && args[1]) {
    const vbf = parseVBF(args[1]);
    const outFile = args[2] || args[1].replace(/\.\w+$/, '.bin');
    if (vbf.compressed) {
        const dec = lzssDecode(vbf.payload);
        fs.writeFileSync(outFile, dec);
        console.log(`Decompressed ${args[1]}: ${vbf.payload.length} -> ${dec.length} bytes`);
        console.log(`Load address: 0x${vbf.addr.toString(16)}`);
        console.log(`Saved to: ${outFile}`);
    } else {
        fs.writeFileSync(outFile, vbf.payload);
        console.log(`Uncompressed VBF, saved raw payload: ${vbf.payload.length} bytes`);
    }
} else if (cmd === 'rebuild' && args[1] && args[2]) {
    const originalVBF = args[1];
    const modifiedBin = args[2];
    const outputVBF = args[3] || originalVBF.replace(/(\.\w+)$/, '_modified$1');

    console.log(`Rebuilding ${path.basename(originalVBF)} with data from ${path.basename(modifiedBin)}`);
    const newData = fs.readFileSync(modifiedBin);
    const output = rebuildVBF(originalVBF, newData);
    fs.writeFileSync(outputVBF, output);
    console.log(`Output: ${outputVBF} (${output.length} bytes)`);

    // Verify by decompressing
    console.log('Verifying...');
    const verify = parseVBF(outputVBF);
    const verifyDec = verify.compressed ? lzssDecode(verify.payload) : verify.payload;
    if (Buffer.compare(verifyDec, newData) === 0) {
        console.log('VERIFIED: Round-trip successful!');
    } else {
        console.log(`WARNING: Verification mismatch! Got ${verifyDec.length} bytes, expected ${newData.length}`);
    }
} else if (cmd === 'info' && args[1]) {
    const vbf = parseVBF(args[1]);
    console.log(`File: ${args[1]}`);
    console.log(`Compressed: ${vbf.compressed}`);
    console.log(`Block address: 0x${vbf.addr.toString(16)}`);
    console.log(`Block length: ${vbf.len} bytes`);
    if (vbf.compressed) {
        const dec = lzssDecode(vbf.payload);
        console.log(`Decompressed size: ${dec.length} bytes`);
    }
} else {
    console.log('VBF Tool - Decompress, modify, and rebuild Ford VBF calibration files');
    console.log('');
    console.log('Usage:');
    console.log('  node vbf_tool.js info <file.VBF>');
    console.log('  node vbf_tool.js decompress <file.VBF> [output.bin]');
    console.log('  node vbf_tool.js rebuild <original.VBF> <modified.bin> [output.VBF]');
    console.log('');
    console.log('Workflow:');
    console.log('  1. decompress the VBF to .bin');
    console.log('  2. Edit the .bin in a hex editor');
    console.log('  3. rebuild to create a new VBF with correct compression and checksums');
}