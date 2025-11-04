from typing import Any
import json
from mcp.server.fastmcp import FastMCP
import httpx
import logging
import sys

# 初始化FastMCP服务器
mcp = FastMCP()
@mcp.tool("fetch_by_construction_daily_nos", description="用 construction_daily_nos 查询符合条件日报")
def fetch_by_construction_daily_nos(
    construction_daily_nos: list[str]) -> str:
    try:
        url=sys.argv[1]
        print(url)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = httpx.post(
            url,
            headers=headers,
            json=construction_daily_nos,
            timeout=30
        )
        response.raise_for_status()
        response_json = response.json()
                # 提取data字段（此时是字符串类型）
        data_str = response_json.get('data')
        return data_str
    except httpx.HTTPError as e:
        print(f"接口调用失败: {e}")
        return ""
    except json.JSONDecodeError:
        print("响应内容不是有效的JSON格式")
        return ""
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

# daily_map = {
#     "DR20251022000086": {
#         "id": 25,
#         "po_no": ["PO25082610030"],
#         "service_work_order_no": ["PN20250826002500"],
#         "construction_daily_no": "DR20251022000086",
#         "construction_daily_paper_no": "CDP20251022000021",
#         "construction_work": "<p>1. On board recheck D/G viscosity sensor ,change connect with M/E sensor the alarm still come ,Therefore, the sensor is judged to be faulty,it suggest replace.</p><p>2. Find the solenoid valve unit panel with C/O,in the pipe passage.</p><p>3. Operation test ballast valve,bilge valve and time check.adjust needle valve .</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [{"name": "DG viscometer sensor", "unit": "个", "factory": "VAF", "quantity": "1"}],
#         "abnormal_defect": "<p>无</p>",
#         "anomaly": [],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251022000090": {
#         "id": 26,
#         "po_no": ["PO25082610030"],
#         "service_work_order_no": ["PN20250826002500"],
#         "construction_daily_no": "DR20251022000090",
#         "construction_daily_paper_no": "CDP20251022000025",
#         "construction_work": "<p>1. Operation test ballast valve,bilge valve and time check.adjust needle valve .</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [{"name": "DG viscometer sensor", "unit": "个", "factory": "VAF", "quantity": "1"}],
#         "abnormal_defect": "<p>无</p>",
#         "anomaly": [],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251027000008": {
#         "id": 34,
#         "po_no": ["PO2508269999"],
#         "service_work_order_no": ["PN20250826001100"],
#         "construction_daily_no": "DR20251027000008",
#         "construction_daily_paper_no": "CDP20251027000006",
#         "construction_work": "<p style=\"text-align: justify;\">1) Replaced spare parts for two lubricators.</p><p style=\"text-align: justify;\">2) Confirmed the construction details of the angular encoder.</p><p style=\"text-align: justify;\">3) Completed the entry formalities.</p><p style=\"text-align: justify;\">4) Checked and counted the spare parts.</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [],
#         "abnormal_defect": "",
#         "anomaly": [{"anomaly": "Plunger spare parts of lubricator not arrived on board.", "anomalyDate": "2025-06-02", "completionDate": "2025-06-21", "disposalResult": "Wait the spare parts."}],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251027000009": {
#         "id": 35,
#         "po_no": ["PO2508269999"],
#         "service_work_order_no": ["PN20250826001100"],
#         "construction_daily_no": "DR20251027000009",
#         "construction_daily_paper_no": "CDP20251027000007",
#         "construction_work": "<p style=\"text-align: justify;\">1) All 6 sets lubricators were disassembled/cleaned/inspected/reassembled, replacement with repair kits.</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [],
#         "abnormal_defect": None,
#         "anomaly": [{"anomaly": "Plunger spare parts of lubricator not arrived on board.", "anomalyDate": "2025-06-21", "completionDate": "2025-06-21", "disposalResult": "Wait for the spare parts."}],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251027000011": {
#         "id": 36,
#         "po_no": ["PO2508269999"],
#         "service_work_order_no": ["PN20250826001100"],
#         "construction_daily_no": "DR20251027000011",
#         "construction_daily_paper_no": "CDP20251027000009",
#         "construction_work": "<p style=\"text-align: justify;\">1) All 6 sets lubricators were reinstalled with new sealing rings.</p><p style=\"text-align: justify;\">2) pick-up sensor was replaced with new spare/function tested, normal working condition.</p><p style=\"text-align: justify;\">3) Angle encoder was replaced with new spare/function tested, normal working condition.</p><p style=\"text-indent: 20pt; text-align: justify;\"> (manual turning of the rotor).</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [],
#         "abnormal_defect": None,
#         "anomaly": [{"anomaly": "Plunger spare parts of lubricator not arrived on board.", "anomalyDate": "2025-06-21", "completionDate": "2025-06-21", "disposalResult": "Wait for the spare parts."}],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251027000013": {
#         "id": 37,
#         "po_no": ["PO2508269999"],
#         "service_work_order_no": ["PN20250826001100"],
#         "construction_daily_no": "DR20251027000013",
#         "construction_daily_paper_no": "CDP20251027000011",
#         "construction_work": "<p style=\"text-align: justify;\">1) All lubricators were function tested, all normal working condition.</p><p style=\"text-align: justify;\">1-1 &nbsp;The air left in the lubricator lines was discharged.</p><p style=\"text-align: justify;\">1-2 &nbsp;All the cylinder lubricator valves were function test inspected from scavenge box, all normal working</p><p style=\"text-indent: 21pt; text-align: justify;\"> condition.</p><p style=\"text-align: justify;\">1-3 &nbsp;The alarm of the lubricators was eliminated under normal working condition.</p>",
#         "vessels_pare_part": [
#             {"name": "Membrane accumulator", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-018", "quantity": "6"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-187", "quantity": "24"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-271", "quantity": "12"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-305", "quantity": "48"},
#             {"name": "Non-return valve", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-317", "quantity": "48"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-329", "quantity": "48"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-342", "quantity": "12"},
#             {"name": "Plunger", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-366", "quantity": "48"},
#             {"name": "Membrane accumulator", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-437", "quantity": "12"},
#             {"name": "Gasket", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-449", "quantity": "12"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-474", "quantity": "12"},
#             {"name": "O-ring", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-486", "quantity": "12"},
#             {"name": "Inductive sensor", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-498", "quantity": "12"},
#             {"name": "Solenoid valve", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-533", "quantity": "12"},
#             {"name": "Cable gland", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-594", "quantity": "12"},
#             {"name": "Cable", "unit": "lubricator ", "factory": "HD -genuine parts", "spareNo": "P90307-0023-604", "quantity": "12"}
#         ],
#         "wk_pare_part": [],
#         "abnormal_defect": None,
#         "anomaly": [{"anomaly": "Plunger spare parts of lubricator not arrived on board.", "anomalyDate": "2025-06-21", "completionDate": "2025-06-21", "disposalResult": "Wait for the spare parts."}],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251029000008": {
#         "id": 41,
#         "po_no": ["PO25082610022"],
#         "service_work_order_no": ["PN20250826002200"],
#         "construction_daily_no": "DR20251029000008",
#         "construction_daily_paper_no": "CDP20251029000007",
#         "construction_work": "<p>1) All units FIVA valves were removed and packing.</p><p>2) All fuel booster dismantled and transferred to workshop,No.4&No.5 fuel booster overhauled,no abnormal found out,piston and plunger were normal condition without scratch.</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [],
#         "abnormal_defect": "<p><span style=\"color: rgb(0, 0, 0);\">1) Lack of spare for fuel booster,sealing ring 4272-0500-0041-138,need 2pcs;</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Lack of spare for fuel booster,section valve 4272-0500-0041-031,need 4pcs.</span></p>",
#         "anomaly": [{"anomaly": "Lack of spare for fuel booster", "anomalyDate": "2025-08-23", "completionDate": "2025-08-23", "disposalResult": "Waiting for Super. confirm"}],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251029000009": {
#         "id": 42,
#         "po_no": ["PO25082610022"],
#         "service_work_order_no": ["PN20250826002200"],
#         "construction_daily_no": "DR20251029000009",
#         "construction_daily_paper_no": "CDP20251029000008",
#         "construction_work": "<p>1) The remaining of fuel booster overhauled,no abnormal found out,piston and plunger were normal condition without scratch.</p><p>2) All 5 pcs fuel booster remounted on HCU,tightened with 1500bar.</p><p>3) Main starting valve and slow turning valve with actuator overhauled,and reassembled complete with repair kits.</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [],
#         "abnormal_defect": "<p><span style=\"color: rgb(0, 0, 0);\">1) Lack of spare for fuel booster,sealing ring Part No.:4272-0500-0041-138,need 2pcs;</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Lack of spare for fuel booster,section valve Part No.:4272-0500-0041-031,need 5pcs.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3)Plate of No.1&amp;No.5 fuel booster have scratch,need to replace.Part No.: 4272-0500-0041-258, 2pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">4) Plate of No.2&amp;No.4 fuel booster have dents,need to replace.Part No.:4272-0500-0041-437, 3pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">5) Driving shaft and shaft bore of main starting valve have scratch,main ball have scratch on air inlet side,and there is much rusty in main starting valve.</span></p><p><span style=\"color: rgb(0, 0, 0);\">Recommendation:</span></p><p><span style=\"color: rgb(0, 0, 0);\">1) Air dry system inspection.</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Air bottle periodic drain.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3) Main ball,Driving shaft and shaft bore polishing and make smooth,reused.But suggest to prepare new main starting valve on board as spare.</span></p>",
#         "anomaly": [
#             {"anomaly": "Lack of spare for fuel booster", "anomalyDate": "2025-08-23", "completionDate": "2025-08-23", "disposalResult": "Waiting for spare delivery"},
#             {"anomaly": "Plate of No.1&No.5 fuel booster have scratch,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Spare waiting for Super. confirm"},
#             {"anomaly": "Plate of No.3&No.4 fuel booster have dents,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Spare waiting for Super. confirm"},
#             {"anomaly": "Driving shaft and shaft bore of main starting valve have scratch", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Polishing and reused"}
#         ],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251029000014": {
#         "id": 45,
#         "po_no": ["PO25082610022"],
#         "service_work_order_no": ["PN20250826002200"],
#         "construction_daily_no": "DR20251029000014",
#         "construction_daily_paper_no": "CDP20251029000013",
#         "construction_work": "<p>1) Fuel booster accessories and pipes assemble completed.</p>",
#         "vessels_pare_part": [{"name": "齿轮", "unit": "个", "remark": "齿轮", "factory": "青岛机械厂，CH1231-123", "spareNo": "372186911", "quantity": "12"}],
#         "wk_pare_part": [],
#         "abnormal_defect": "<p><span style=\"color: rgb(0, 0, 0);\">1) Lack of spare for fuel booster,sealing ring Part No.:4272-0500-0041-138,need 2pcs;</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Lack of spare for fuel booster,section valve Part No.:4272-0500-0041-031,need 5pcs.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3)Plate of No.1&amp;No.5 fuel booster have scratch,need to replace.Part No.: 4272-0500-0041-258, 2pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">4) Plate of No.2&amp;No.4 fuel booster have dents,need to replace.Part No.:4272-0500-0041-437, 3pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">5) Driving shaft and shaft bore of main starting valve have scratch,main ball have scratch on air inlet side,and there is much rusty in main starting valve.</span></p><p><span style=\"color: rgb(0, 0, 0);\">Recommendation:</span></p><p><span style=\"color: rgb(0, 0, 0);\">1) Air dry system inspection.</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Air bottle periodic drain.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3) Main ball,Driving shaft and shaft bore polishing and make smooth,reused.But suggest to prepare new main starting valve on board as spare.</span></p>",
#         "anomaly": [
#             {"anomaly": "Lack of spare for fuel booster", "anomalyDate": "2025-08-23", "completionDate": "2025-08-23", "disposalResult": "Waiting for spare delivery"},
#             {"anomaly": "Plate of No.1&No.5 fuel booster have scratch,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Spare waiting for Super. confirm"},
#             {"anomaly": "Plate of No.3&No.4 fuel booster have dents,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Spare waiting for Super. confirm"},
#             {"anomaly": "Driving shaft and shaft bore of main starting valve have scratch", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Polishing and reused"}
#         ],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     },
#     "DR20251029000020": {
#         "id": 47,
#         "po_no": ["PO25082610022"],
#         "service_work_order_no": ["PN20250826002200"],
#         "construction_daily_no": "DR20251029000020",
#         "construction_daily_paper_no": "CDP20251029000019",
#         "construction_work": "<p>1） FIVA assembled with new sealing rings,bolts tightened by 75Nm,cable re-connected;</p><p>2） Fore and aft chain were re-tightened according to manual book instruction.</p>",
#         "vessels_pare_part": [],
#         "wk_pare_part": [
#             {"name": "Proportional valve of FIVA ", "unit": "PCS", "factory": "Nabtesco,NFSV-01-25", "spareNo": "", "quantity": "6"},
#             {"name": "Section v/v of fuel booster", "unit": "PCS", "spareNo": "4272-0500-0041-031", "quantity": "5"},
#             {"name": "Sealing ring of fuel booster", "unit": "PCS", "spareNo": "4272-0500-0041-138", "quantity": "2"},
#             {"name": "Plate of fuel booster", "unit": "PCS", "spareNo": "4272-0500-0041-258", "quantity": "2"},
#             {"name": "Plate of fuel booster", "unit": "PCS", "spareNo": "4272-0500-0041-437", "quantity": "3"}
#         ],
#         "abnormal_defect": "<p><span style=\"color: rgb(0, 0, 0);\">1) Lack of spare for fuel booster,sealing ring Part No.:4272-0500-0041-138,need 2pcs;</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Lack of spare for fuel booster,section valve Part No.:4272-0500-0041-031,need 5pcs.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3)Plate of No.1&amp;No.5 fuel booster have scratch,need to replace.Part No.: 4272-0500-0041-258, 2pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">4) Plate of No.2&amp;No.4 fuel booster have dents,need to replace.Part No.:4272-0500-0041-437, 3pcs</span></p><p><span style=\"color: rgb(0, 0, 0);\">5) Driving shaft and shaft bore of main starting valve have scratch,main ball have scratch on air inlet side,and there is much rusty in main starting valve.</span></p><p><span style=\"color: rgb(0, 0, 0);\">Recommendation:</span></p><p><span style=\"color: rgb(0, 0, 0);\">1) Air dry system inspection.</span></p><p><span style=\"color: rgb(0, 0, 0);\">2) Air bottle periodic drain.</span></p><p><span style=\"color: rgb(0, 0, 0);\">3) Main ball,Driving shaft and shaft bore polishing and make smooth,reused.But suggest to prepare new main starting valve on board as spare.</span></p>",
#         "anomaly": [
#             {"anomaly": "Lack of spare for fuel booster", "anomalyDate": "2025-08-23", "completionDate": "2025-08-27", "disposalResult": "Done "},
#             {"anomaly": "Plate of No.1&No.5 fuel booster have scratch,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-27", "disposalResult": "Done "},
#             {"anomaly": "Plate of No.3&No.4 fuel booster have dents,need to replace", "anomalyDate": "2025-08-24", "completionDate": "2025-08-27", "disposalResult": "Done "},
#             {"anomaly": "Driving shaft and shaft bore of main starting valve have scratch", "anomalyDate": "2025-08-24", "completionDate": "2025-08-24", "disposalResult": "Polishing and reused"}
#         ],
#         "future_operational_matter": None,
#         "outstanding_item": None
#     }
#     }

# @mcp.tool("fetch_by_construction_daily_nos", description="用 construction_daily_nos 查询符合条件日报")
# def fetch_by_construction_daily_nos(
#     construction_daily_nos: list[str]) -> str:
    
#     result = [daily_map[no] for no in construction_daily_nos if no in daily_map]
#     result_json = json.dumps(result, ensure_ascii=False, indent=2)
#     return result_json
# zkkdaily

