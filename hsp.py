#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HSP 语言解释器 - 最终稳定版
修复变量引用、条件判断、循环记录
"""

import re
import random
import math
import time


class HSP:
    def __init__(self):
        self.pools = {}      # 池子
        self.vars = {}       # 变量
        self.output = []     # 输出
        self.stats = {
            'draws': 0,
            'success': 0,
            'start_time': None,
            'lines': 0
        }
        self.last_record = {}  # 上次循环记录结果
    
    # ==================== 概率解析 ====================
    
    def parse_prob(self, prob_str):
        """解析概率（支持科学计数法）"""
        prob_str = prob_str.strip()
        
        # 科学计数法: 1.7/-97
        if '/-' in prob_str:
            parts = prob_str.split('/-')
            return float(parts[0]) * (10 ** -int(parts[1]))
        
        # 科学计数法: 1.7/+80
        if '/+' in prob_str:
            parts = prob_str.split('/+')
            return float(parts[0]) * (10 ** int(parts[1]))
        
        # 普通百分比: 0.6/
        if prob_str.endswith('/'):
            return float(prob_str[:-1])
        
        return float(prob_str)
    
    # ==================== 变量处理 ====================
    
    def get_var(self, name):
        """获取变量值"""
        if name.startswith('#'):
            name = name[1:]
        return self.vars.get(name, 0)
    
    def set_var(self, name, value):
        """设置变量值"""
        if name.startswith('#'):
            name = name[1:]
        self.vars[name] = value
        return value
    
    def format_text(self, text):
        """格式化文本（替换变量）"""
        def replace_var(match):
            var_name = match.group(1)
            val = self.vars.get(var_name, match.group(0))
            if isinstance(val, float):
                if abs(val) < 0.001 or abs(val) > 1e6:
                    return f"{val:.2e}"
                return f"{val:.4f}".rstrip('0').rstrip('.')
            return str(val)
        
        return re.sub(r'#(\w+)', replace_var, text)
    
    # ==================== 主执行 ====================
    
    def run(self, code):
        """运行HSP代码"""
        self.output = []
        self.stats['start_time'] = time.time()
        self.stats['lines'] = 0
        
        lines = code.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            
            if not line or line.startswith('¢'):
                continue
            
            self.stats['lines'] += 1
            try:
                self.execute_line(line)
            except Exception as e:
                self.print(f"❌ 错误: {e}")
        
        return self.output
    
    def execute_line(self, line):
        """执行单行"""
        # 输出指令
        if line.startswith('¢,'):
            text = self.format_text(line[2:].strip())
            self.print(text)
        
        # 池子定义
        elif ')#' in line and ':/' in line:
            self.define_pool(line)
        
        # 目标声明
        elif line.startswith('<') and '*,' in line:
            self.execute_goal(line)
        
        # 变量赋值
        elif line.startswith('#') and '=' in line:
            self.assign_var(line)
        
        # 数学运算
        elif line.startswith('&A('):
            result = self.eval_math(line)
            self.print(f"= {self.format_value(result)}")
        
        # 循环记录
        elif line.startswith('#¢{') and '}±' in line:
            self.loop_record(line)
        
        # 显示统计
        elif line == '#stats':
            self.show_stats()
        
        # 清空变量
        elif line == '#clear':
            self.vars.clear()
            self.print("🧹 变量已清空")
        
        # 条件判断
        elif line.startswith('?') and '⇒' in line:
            self.execute_condition(line)
        
        else:
            self.print(f"⏳ {line}")
    
    # ==================== 池子操作 ====================
    
    def define_pool(self, line):
        """定义池子"""
        # 移除空格
        line = re.sub(r'\s+', '', line)
        match = re.match(r'\((.+?):/(.+?)\)#(.+)', line)
        
        if match:
            prob_str, items_str, name = match.groups()
            item_list = [i.strip() for i in items_str.split(',')]
            
            prob = self.parse_prob(prob_str)
            per_item = prob / len(item_list)
            
            self.pools[name] = {
                'prob': prob,
                'items': item_list,
                'per_item': per_item
            }
            self.print(f"📦 池子 '{name}' ({len(item_list)}件, {prob}%)")
        else:
            self.print(f"⚠️ 池子格式错误: {line}")
    
    # ==================== 目标声明 ====================
    
    def execute_goal(self, line):
        """执行目标声明"""
        # 移除空格
        line = re.sub(r'\s+', '', line)
        match = re.search(r'<\$(.+?),#(.+?)[×*](\d+),\*(\d+)>', line)
        
        if match:
            item, pool_name, draw_type, guarantee = match.groups()
            
            if pool_name not in self.pools:
                self.print(f"❌ 池子 '{pool_name}' 不存在")
                return
            
            pool = self.pools[pool_name]
            draw_times = int(draw_type)
            guarantee_num = int(guarantee)
            
            self.print(f"🎯 目标: {item} {guarantee_num}抽保底 ({draw_times}连)")
            
            # 模拟抽卡
            draws = 0
            for i in range(1, guarantee_num + 1, draw_times):
                draws = min(i + draw_times - 1, guarantee_num)
                
                if random.random() * 100 < pool['per_item']:
                    self.print(f"✨ 第{draws}抽抽到 {item}！")
                    self.stats['success'] += 1
                    self.stats['draws'] += draws
                    # 设置变量表示抽到了
                    self.set_var(f"${item}", 1)
                    return
                
                if draws % 10 == 0:
                    self.print(f"⏳ 已抽{draws}抽...")
            
            self.print(f"🎯 保底: 第{guarantee_num}抽获得 {item}")
            self.stats['draws'] += guarantee_num
            self.set_var(f"${item}", 1)
        else:
            self.print(f"⚠️ 目标格式错误: {line}")
    
    # ==================== 变量赋值 ====================
    
    def assign_var(self, line):
        """变量赋值"""
        match = re.match(r'#(.+?)\s*=\s*(.+)', line)
        if match:
            name, value_str = match.groups()
            
            # 处理特殊变量 #¢.rate
            if value_str == '#¢.rate' and 'last_record' in self.__dict__:
                value = self.last_record.get('rate', 0)
            else:
                # 解析值
                if value_str.startswith('&A('):
                    value = self.eval_math(value_str)
                elif value_str.startswith('"') and value_str.endswith('"'):
                    value = value_str[1:-1]
                else:
                    try:
                        value = float(value_str)
                    except:
                        value = value_str
            
            self.set_var(name, value)
            self.print(f"📊 #{name} = {self.format_value(value)}")
    
    # ==================== 数学运算 ====================
    
    def eval_math(self, expr):
        """计算数学表达式"""
        expr = expr[3:-1]  # 去掉 &A( 和 )
        
        # 替换符号
        expr = expr.replace('×', '*').replace('÷', '/').replace('^', '**')
        expr = expr.replace('π', str(math.pi)).replace('e', str(math.e))
        
        # 替换变量
        def replace_var(match):
            var_name = match.group(1)
            return str(self.vars.get(var_name, 0))
        expr = re.sub(r'#(\w+)', replace_var, expr)
        
        # 数学函数
        expr = expr.replace('㏒', 'math.log10')
        expr = expr.replace('㏑', 'math.log')
        expr = expr.replace('√', 'math.sqrt')
        expr = expr.replace('abs', 'math.fabs')
        
        try:
            # 安全求值
            result = eval(expr, {"__builtins__": {}, "math": math})
            return float(result)
        except Exception as e:
            self.print(f"⚠️ 数学计算错误: {e}")
            return 0
    
    # ==================== 循环记录 ====================
    
    def loop_record(self, line):
        """循环记录 #¢{操作}± (次数)"""
        match = re.match(r'#¢\{(.+?)\}±\s*\((\d+)\)', line)
        if match:
            operation, times = match.groups()
            times = int(times)
            
            self.print(f"🔄 循环 {times} 次")
            
            success = 0
            for i in range(times):
                # 简单模拟成功率 50% 左右
                if random.random() < 0.5:
                    success += 1
                
                if (i + 1) % max(1, times // 10) == 0:
                    progress = (i + 1) / times * 100
                    self.print(f"⏳ {progress:.0f}% ({i+1}/{times})")
            
            rate = success / times * 100
            self.print(f"📊 成功率: {rate:.1f}% ({success}/{times})")
            
            # 存储结果
            self.last_record = {
                'success': success,
                'total': times,
                'rate': rate
            }
            
            # 设置变量 #¢.success #¢.total #¢.rate
            self.set_var('¢.success', success)
            self.set_var('¢.total', times)
            self.set_var('¢.rate', rate)
    
    # ==================== 条件判断 ====================
    
    def execute_condition(self, line):
        """执行条件判断 ?(条件) ⇒ 动作"""
        match = re.match(r'\?\((.+?)\)\s*⇒\s*(.+)', line)
        if match:
            condition, action = match.groups()
            
            # 评估条件
            result = self.eval_condition(condition)
            
            if result:
                self.print(f"✅ 条件成立，执行: {action}")
                self.execute_line(action)
            else:
                self.print(f"⏭️ 条件不成立")
    
    def eval_condition(self, cond):
        """评估条件表达式"""
        # 处理 #变量 > #变量 或 #变量 > 数字
        ops = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b
        }
        
        for op in ops:
            if op in cond:
                parts = cond.split(op)
                if len(parts) == 2:
                    left = self.eval_value(parts[0].strip())
                    right = self.eval_value(parts[1].strip())
                    return ops[op](left, right)
        
        return False
    
    def eval_value(self, token):
        """评估单个值（变量或数字）"""
        token = token.strip()
        if token.startswith('&A('):
            return self.eval_math(token)
        elif token.startswith('#'):
            return self.vars.get(token[1:], 0)
        else:
            try:
                return float(token)
            except:
                return token
    
    # ==================== 统计 ====================
    
    def show_stats(self):
        """显示统计信息"""
        duration = time.time() - self.stats['start_time']
        print("\n" + "=" * 50)
        print("📊 统计信息")
        print("=" * 50)
        print(f"运行时间: {duration:.2f}秒")
        print(f"执行行数: {self.stats['lines']}")
        print(f"总抽卡: {self.stats['draws']}")
        if self.stats['draws'] > 0:
            rate = self.stats['success'] / self.stats['draws'] * 100
            print(f"成功率: {rate:.4f}%")
        print(f"变量数: {len(self.vars)}")
        print(f"池子数: {len(self.pools)}")
        
        if self.vars:
            print("\n📋 变量列表:")
            for name, val in list(self.vars.items())[:10]:
                print(f"  #{name} = {self.format_value(val)}")
        
        print("=" * 50)
    
    # ==================== 工具 ====================
    
    def format_value(self, val):
        """格式化值"""
        if isinstance(val, float):
            if abs(val) < 0.001 or abs(val) > 1e6:
                return f"{val:.2e}"
            return f"{val:.4f}".rstrip('0').rstrip('.')
        return str(val)
    
    def print(self, text):
        """输出"""
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] {text}")
        self.output.append(text)


# ==================== 命令行 ====================

def main():
    import sys
    import os
    
    hsp = HSP()
    
    # 交互模式
    if len(sys.argv) == 1 or '-i' in sys.argv:
        print("=" * 50)
        print("HSP 最终稳定版")
        print("命令: #stats 统计, #clear 清空, exit 退出")
        print("=" * 50)
        
        while True:
            try:
                line = input("\nHSP> ").strip()
                if line.lower() in ('exit', 'quit'):
                    break
                if not line:
                    continue
                hsp.execute_line(line)
            except KeyboardInterrupt:
                print("\n退出")
                break
    
    # 执行代码
    elif '-e' in sys.argv:
        idx = sys.argv.index('-e')
        if idx + 1 < len(sys.argv):
            code = sys.argv[idx + 1]
            hsp.run(code)
    
    # 执行文件
    elif len(sys.argv) == 2 and sys.argv[1] != '--help':
        filename = sys.argv[1]
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                hsp.run(f.read())
        else:
            print(f"文件不存在: {filename}")
    
    else:
        print("用法:")
        print("  python hsp.py 文件.hps")
        print("  python hsp.py -e '代码'")
        print("  python hsp.py -i")


if __name__ == '__main__':
    main()
