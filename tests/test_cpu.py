#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cpu
----------------------------------

Tests for `py65emu` module.
"""

import unittest

from py65emu.cpu import CPU
from py65emu.mmu import MMU

class TestCPU(unittest.TestCase):

    def _cpu(self, ram=(0,0x200, False), rom=(0x1000, 0x100), romInit=None, pc=0x1000):
        return CPU(
            MMU([
                ram,
                rom + (True,romInit)
            ]),
            pc
        )

    def setUp(self):
        pass

    def test_fromBCD(self):
        c = self._cpu()
        self.assertEqual(c.fromBCD(0), 0)
        self.assertEqual(c.fromBCD(0x05), 5)
        self.assertEqual(c.fromBCD(0x11), 11)
        self.assertEqual(c.fromBCD(0x99), 99)

    def test_toBCD(self):
        c = self._cpu()
        self.assertEqual(c.toBCD(0), 0)
        self.assertEqual(c.toBCD(5), 0x05)
        self.assertEqual(c.toBCD(11), 0x11)
        self.assertEqual(c.toBCD(99), 0x99)

    def test_fromTwosCom(self):
        c = self._cpu()
        self.assertEqual(c.fromTwosCom(0x00), 0)
        self.assertEqual(c.fromTwosCom(0x01), 1)
        self.assertEqual(c.fromTwosCom(0x7f), 127)
        self.assertEqual(c.fromTwosCom(0xff), -1)
        self.assertEqual(c.fromTwosCom(0x80), -128)
        
    def test_nextByte(self):
        c = self._cpu(romInit=[1, 2, 3])
        self.assertEqual(c.nextByte(), 1)
        self.assertEqual(c.nextByte(), 2)
        self.assertEqual(c.nextByte(), 3)
        self.assertEqual(c.nextByte(), 0)

    def test_nextWord(self):
        c = self._cpu(romInit=[1, 2, 3, 4, 5, 9, 10])
        self.assertEqual(c.nextWord(), 0x0201)
        c.nextByte()
        self.assertEqual(c.nextWord(), 0x0504)
        self.assertEqual(c.nextWord(), 0x0a09)

    def test_zeropage_addressing(self):
        c = self._cpu(romInit=[1, 2, 3, 4, 5])
        self.assertEqual(c.z_a(), 1)
        c.r.x = 0
        self.assertEqual(c.zx_a(), 2)
        c.r.x = 1
        self.assertEqual(c.zx_a(), 4)
        c.r.y = 0
        self.assertEqual(c.zy_a(), 4)
        c.r.y = 1
        self.assertEqual(c.zy_a(), 6)

    def test_absolute_addressing(self):
        c = self._cpu(romInit=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(c.a_a(), 0x0201)

        c.r.x = 0
        c.cc = 0
        self.assertEqual(c.ax_a(), 0x0403)
        self.assertEqual(c.cc, 0)
        c.r.x = 0xff
        c.cc = 0
        self.assertEqual(c.ax_a(), 0x0605+0xff)
        self.assertEqual(c.cc, 1)

        c.r.y = 0
        c.cc = 0
        self.assertEqual(c.ay_a(), 0x0807)
        self.assertEqual(c.cc, 0)
        c.r.y = 0xff
        c.cc = 0
        self.assertEqual(c.ay_a(), 0x0a09+0xff)
        self.assertEqual(c.cc, 1)

    def test_indirect_addressing(self):
        c = self._cpu(romInit=[
            0x08, 0x10,
            0xff, 0x10,
            0x00, 0x10,
            0x0c, 0x10,

            0xf0, 0x00,
            0xe0, 0x00,
            0xd0, 0x00,
        ])

        self.assertEqual(c.i_a(), 0x00f0)
        self.assertEqual(c.i_a(), 0x0800)
        c.r.x = 0x0a
        self.assertEqual(c.ix_a(), 0x00e0)
        c.r.y = 0x0f
        self.assertEqual(c.iy_a(), 0x00df)

    def test_stack(self):
        c = self._cpu()
        c.stackPush(0x10)
        self.assertEqual(c.stackPop(), 0x10)
        c.stackPushWord(0x0510)
        self.assertEqual(c.stackPopWord(), 0x0510)
        self.assertEqual(c.stackPop(), 0x00)
        c.stackPush(0x00)
        c.stackPushWord(0x0510)
        self.assertEqual(c.stackPop(), 0x10)
        self.assertEqual(c.stackPop(), 0x05)


    def test_adc(self):
        c = self._cpu(romInit=[1, 2, 250, 3, 100, 100])

        #immediate
        c.ops[0x69]()
        self.assertEqual(c.r.a, 1)
        c.ops[0x69]()
        self.assertEqual(c.r.a, 3)
        c.ops[0x69]()
        self.assertEqual(c.r.a, 253)
        self.assertTrue(c.r.getFlag('N'))
        c.r.clearFlags()
        c.ops[0x69]()
        self.assertTrue(c.r.getFlag('C'))
        self.assertTrue(c.r.getFlag('Z'))
        c.r.clearFlags()
        c.ops[0x69]()
        c.ops[0x69]()
        self.assertTrue(c.r.getFlag('V'))

    def test_adc_decimal(self):
        c = self._cpu(romInit=[0x01, 0x55, 0x50])
        c.r.setFlag('D')

        c.ops[0x69]()
        self.assertEqual(c.r.a, 0x01)
        c.ops[0x69]()
        self.assertEqual(c.r.a, 0x56)
        c.ops[0x69]()
        self.assertEqual(c.r.a, 0x06)
        self.assertTrue(c.r.getFlag('C'))

    def test_and(self):
        c = self._cpu(romInit=[0xff, 0xff, 0x01, 0x2])

        c.r.a = 0x00
        c.ops[0x29]()
        self.assertEqual(c.r.a, 0)

        c.r.a = 0xff
        c.ops[0x29]()
        self.assertEqual(c.r.a, 0xff)

        c.r.a = 0x01
        c.ops[0x29]()
        self.assertEqual(c.r.a, 0x01)

        c.r.a = 0x01
        c.ops[0x29]()
        self.assertEqual(c.r.a, 0x00)

    def test_asl(self):
        c = self._cpu(romInit=[0x00])

        c.r.a = 1
        c.ops[0x0a]()
        self.assertEqual(c.r.a, 2)

        c.mmu.write(0, 4)
        c.ops[0x06]()
        self.assertEqual(c.mmu.read(0), 8)

    def test_bit(self):
        c = self._cpu(romInit=[0x00, 0x00, 0x10])
        c.mmu.write(0, 0xff)
        c.r.a = 1

        c.ops[0x24]() #Zero page
        self.assertFalse(c.r.getFlag('Z'))
        self.assertTrue(c.r.getFlag('N'))
        self.assertTrue(c.r.getFlag('V'))

        c.ops[0x2c]() #Absolute
        self.assertTrue(c.r.getFlag('Z'))
        self.assertFalse(c.r.getFlag('N'))
        self.assertFalse(c.r.getFlag('V'))

    def test_brk(self):
        c = self._cpu()
        c.mmu.addBlock(0xfffe, 0x2, True, [0x34, 0x12])
        c.r.p = 239
        c.ops[0x00]()
        self.assertTrue(c.r.getFlag('B'))
        self.assertFalse(c.r.getFlag('I'))
        self.assertEqual(c.r.pc, 0x1234)
        self.assertEqual(c.stackPop(), 255)
        self.assertEqual(c.stackPopWord(), 0x1001)

    def test_branching(self):
        c = self._cpu(romInit=[0x01, 0x00, 0x00, 0xfc])
        c.ops[0x10]()
        self.assertEqual(c.r.pc, 0x1002)
        c.ops[0x70]()
        self.assertEqual(c.r.pc, 0x1003)
        c.r.setFlag('C')
        c.ops[0xb0]()
        self.assertEqual(c.r.pc, 0x1000)
        c.ops[0xd0]()
        self.assertEqual(c.r.pc, 0x1002)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()