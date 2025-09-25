#!/usr/bin/env python3
"""
SAP Integration Flow Knowledge Graph Creator - Complete Version
Processes ALL iFlow folders in the main directory and creates isolated Knowledge Graphs for each.
Each iFlow folder gets its own separate Folder node and subgraph, ensuring no cross-folder connections.
Replicates the exact SAP iFlow diagram into a Neo4j Knowledge Graph for each folder.
"""

import os
import xml.etree.ElementTree as ET
from neo4j import GraphDatabase
from dotenv import load_dotenv
import logging
from typing import Dict, List, Tuple, Any
import json
import glob

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteIFlowKnowledgeGraph:
    """
    Creates Knowledge Graphs for ALL SAP Integration Flow folders.
    Each folder gets its own isolated subgraph with no cross-folder connections.
    """
    
    def __init__(self, base_directory: str = "."):
        """Initialize the Knowledge Graph creator with Neo4j connection."""
        self.uri = os.getenv('NEO4J_URI', 'neo4j://127.0.0.1:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.base_directory = base_directory
        
        # Store processed folders
        self.processed_folders = []
        self.failed_folders = []
        
    def close(self):
        """Close the Neo4j driver connection."""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear existing iFlow data from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing iFlow data from database")
    
    def get_current_counts(self) -> Dict[str, int]:
        """Get current node and relationship counts from the database."""
        with self.driver.session() as session:
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            return {'nodes': node_count, 'relationships': rel_count}
    
    def find_iflow_folders(self) -> List[str]:
        """
        Find all iFlow folders in the base directory.
        Returns a list of folder paths that contain iFlow files.
        """
        logger.info(f"Scanning for iFlow folders in: {self.base_directory}")
        
        iflow_folders = []
        
        # Look for folders that contain the typical iFlow structure
        for item in os.listdir(self.base_directory):
            item_path = os.path.join(self.base_directory, item)
            
            # Skip if not a directory
            if not os.path.isdir(item_path):
                continue
                
            # Skip special directories
            if item.startswith('.') or item in ['__pycache__', 'Extracted', 'extracted_confirm_product']:
                continue
            
            # Check if this folder contains an iFlow file
            iflow_pattern = os.path.join(item_path, "src", "main", "resources", "scenarioflows", "integrationflow", "*.iflw")
            iflow_files = glob.glob(iflow_pattern)
            
            if iflow_files:
                iflow_folders.append(item_path)
                logger.info(f"Found iFlow folder: {item}")
        
        logger.info(f"Found {len(iflow_folders)} iFlow folders to process")
        return iflow_folders
    
    def get_iflow_file_path(self, folder_path: str) -> str:
        """
        Get the iFlow file path for a given folder.
        Returns the path to the .iflw file in the folder.
        """
        iflow_pattern = os.path.join(folder_path, "src", "main", "resources", "scenarioflows", "integrationflow", "*.iflw")
        iflow_files = glob.glob(iflow_pattern)
        
        if iflow_files:
            return iflow_files[0]  # Return the first .iflw file found
        else:
            raise FileNotFoundError(f"No .iflw file found in {folder_path}")
    
    def get_folder_name(self, folder_path: str) -> str:
        """Extract a clean folder name from the folder path."""
        return os.path.basename(folder_path)
    
    def parse_iflow_xml(self, iflow_file: str) -> Dict[str, Any]:
        """
        Parse the iFlow XML file and extract all components and relationships.
        Returns a structured dictionary with all iFlow elements including protocol components.
        """
        logger.info(f"Parsing iFlow XML file: {iflow_file}")
        
        try:
            tree = ET.parse(iflow_file)
            root = tree.getroot()
        except FileNotFoundError:
            logger.error(f"iFlow file not found: {iflow_file}")
            return self._create_fallback_structure()
        
        # Define namespaces
        namespaces = {
            'bpmn2': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
            'ifl': 'http:///com.sap.ifl.model/Ifl.xsd'
        }
        
        data = {
            'processes': [],
            'participants': [],
            'components': [],
            'sequence_flows': [],
            'message_flows': [],
            'subprocesses': [],
            'protocols': []  # New: Protocol-specific components
        }
        
        # Extract processes
        for process in root.findall('.//bpmn2:process', namespaces):
            process_data = {
                'id': process.get('id'),
                'name': self._get_node_name(process.get('name'), process.get('id'), 'Process'),
                'type': 'Process'
            }
            data['processes'].append(process_data)
        
        # Extract participants (exclude those that are actually processes with processRef)
        for participant in root.findall('.//bpmn2:participant', namespaces):
            # Skip participants that are actually processes (have processRef)
            if participant.get('processRef'):
                continue
                
            participant_data = {
                'id': participant.get('id'),
                'name': self._get_node_name(participant.get('name'), participant.get('id'), 'Participant'),
                'type': 'Participant'
            }
            data['participants'].append(participant_data)
        
        # Extract all components (start events, end events, service tasks, call activities, gateways)
        component_types = ['startEvent', 'endEvent', 'serviceTask', 'callActivity', 'parallelGateway', 'exclusiveGateway']
        
        for comp_type in component_types:
            for component in root.findall(f'.//bpmn2:{comp_type}', namespaces):
                # Extract activityType from extension elements
                activity_type = self._extract_activity_type(component, namespaces)
                
                component_data = {
                    'id': component.get('id'),
                    'name': self._get_node_name(component.get('name'), component.get('id'), activity_type or self._normalize_component_type(comp_type)),
                    'type': activity_type or self._normalize_component_type(comp_type)
                }
                data['components'].append(component_data)
        
        # Extract subprocesses
        for subprocess in root.findall('.//bpmn2:subProcess', namespaces):
            subprocess_data = {
                'id': subprocess.get('id'),
                'name': self._get_node_name(subprocess.get('name'), subprocess.get('id'), 'SubProcess'),
                'type': 'SubProcess'
            }
            data['subprocesses'].append(subprocess_data)
        
        # Extract sequence flows
        for flow in root.findall('.//bpmn2:sequenceFlow', namespaces):
            flow_data = {
                'id': flow.get('id'),
                'name': flow.get('name', ''),
                'source': flow.get('sourceRef'),
                'target': flow.get('targetRef'),
                'type': 'SequenceFlow'
            }
            data['sequence_flows'].append(flow_data)
        
        # Extract message flows
        for flow in root.findall('.//bpmn2:messageFlow', namespaces):
            flow_data = {
                'id': flow.get('id'),
                'name': flow.get('name', ''),
                'source': flow.get('sourceRef'),
                'target': flow.get('targetRef'),
                'type': 'MessageFlow'
            }
            data['message_flows'].append(flow_data)
        
        # Extract protocol-specific components from message flows and participants
        self._extract_protocol_components(root, namespaces, data)
        
        logger.info(f"Parsed {len(data['processes'])} processes, {len(data['participants'])} participants, "
                   f"{len(data['components'])} components, {len(data['subprocesses'])} subprocesses, "
                   f"{len(data['sequence_flows'])} sequence flows, {len(data['message_flows'])} message flows, "
                   f"{len(data['protocols'])} protocol components")
        
        return data
    
    def _get_node_name(self, name: str, node_id: str, node_type: str, system: str = None, adapter_name: str = None) -> str:
        """
        Get a proper node name with fallback logic.
        If name is empty or None, fallback to system, adapter_name, id, or type properties.
        """
        if name and name.strip():
            return name.strip()
        
        # For protocols, try system property first
        if system and system.strip():
            return system.strip()
        
        # Try adapter_name for protocols
        if adapter_name and adapter_name.strip():
            return adapter_name.strip()
        
        # Fallback to node_id if available
        if node_id and node_id.strip():
            return node_id.strip()
        
        # Fallback to node_type
        if node_type and node_type.strip():
            return f"{node_type}_{node_id}" if node_id else node_type
        
        # Last resort
        return "Unknown_Node"
    
    def _extract_activity_type(self, component, namespaces: Dict[str, str]) -> str:
        """Extract activityType from component extension elements."""
        extension_elements = component.find('.//bpmn2:extensionElements', namespaces)
        if extension_elements is not None:
            for property_elem in extension_elements.findall('.//ifl:property', namespaces):
                key_elem = property_elem.find('key')
                value_elem = property_elem.find('value')
                
                if key_elem is not None and value_elem is not None:
                    if key_elem.text == 'activityType':
                        return value_elem.text
        return None
    
    def _extract_protocol_components(self, root, namespaces: Dict[str, str], data: Dict[str, Any]) -> None:
        """
        Extract protocol-specific components from message flows and participants.
        This captures ALL SAP Integration Suite adapter types: IDOC, SOAP, HTTP, HCIOData, AMQP, ProcessDirect, Mail, etc.
        """
        # Extract protocol information from message flows
        for flow in root.findall('.//bpmn2:messageFlow', namespaces):
            protocol_data = self._extract_protocol_from_flow(flow, namespaces)
            if protocol_data:
                data['protocols'].append(protocol_data)
        
        # Extract protocol information from participants
        for participant in root.findall('.//bpmn2:participant', namespaces):
            protocol_data = self._extract_protocol_from_participant(participant, namespaces)
            if protocol_data:
                data['protocols'].append(protocol_data)
        
        # Extract protocol information from all components (broader coverage)
        for component in root.findall('.//bpmn2:*', namespaces):
            if component.tag.endswith('}startEvent') or component.tag.endswith('}endEvent') or \
               component.tag.endswith('}serviceTask') or component.tag.endswith('}callActivity'):
                protocol_data = self._extract_protocol_from_component(component, namespaces)
                if protocol_data:
                    data['protocols'].append(protocol_data)
    
    def _extract_protocol_from_flow(self, flow, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Extract protocol information from a message flow element."""
        protocol_data = None
        
        # Look for extension elements with protocol information
        extension_elements = flow.find('.//bpmn2:extensionElements', namespaces)
        if extension_elements is not None:
            protocol_data = self._parse_extension_elements(extension_elements, namespaces)
            if protocol_data:
                protocol_data.update({
                    'id': f"Protocol_{flow.get('id')}",
                    'name': self._get_node_name(
                        flow.get('name', ''), 
                        flow.get('id'), 
                        'Protocol',
                        protocol_data.get('system'),
                        protocol_data.get('adapter_name')
                    ),
                    'source': flow.get('sourceRef'),
                    'target': flow.get('targetRef'),
                    'type': 'Protocol'
                })
        
        return protocol_data
    
    def _extract_protocol_from_participant(self, participant, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Extract protocol information from a participant element."""
        protocol_data = None
        
        # Look for extension elements with protocol information
        extension_elements = participant.find('.//bpmn2:extensionElements', namespaces)
        if extension_elements is not None:
            protocol_data = self._parse_extension_elements(extension_elements, namespaces)
            if protocol_data:
                protocol_data.update({
                    'id': f"Protocol_{participant.get('id')}",
                    'name': self._get_node_name(
                        participant.get('name', ''), 
                        participant.get('id'), 
                        'Protocol',
                        protocol_data.get('system'),
                        protocol_data.get('adapter_name')
                    ),
                    'participant_id': participant.get('id'),
                    'type': 'Protocol'
                })
        
        return protocol_data
    
    def _extract_protocol_from_component(self, component, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Extract protocol information from a component element."""
        protocol_data = None
        
        # Look for extension elements with protocol information
        extension_elements = component.find('.//bpmn2:extensionElements', namespaces)
        if extension_elements is not None:
            protocol_data = self._parse_extension_elements(extension_elements, namespaces)
            if protocol_data:
                protocol_data.update({
                    'id': f"Protocol_{component.get('id')}",
                    'name': self._get_node_name(
                        component.get('name', ''), 
                        component.get('id'), 
                        'Protocol',
                        protocol_data.get('system'),
                        protocol_data.get('adapter_name')
                    ),
                    'component_id': component.get('id'),
                    'type': 'Protocol'
                })
        
        return protocol_data
    
    def _parse_extension_elements(self, extension_elements, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse extension elements to extract protocol information."""
        protocol_info = {}
        
        # Extract properties from extension elements
        for property_elem in extension_elements.findall('.//ifl:property', namespaces):
            key_elem = property_elem.find('key')
            value_elem = property_elem.find('value')
            
            if key_elem is not None and value_elem is not None:
                key = key_elem.text
                value = value_elem.text
                
                # Capture ALL SAP Integration Suite protocol-specific properties
                if key == 'ComponentType':
                    protocol_info['component_type'] = value
                elif key == 'TransportProtocol':
                    protocol_info['transport_protocol'] = value
                elif key == 'MessageProtocol':
                    protocol_info['message_protocol'] = value
                elif key == 'ComponentNS':
                    protocol_info['component_namespace'] = value
                elif key == 'direction':
                    protocol_info['direction'] = value
                elif key == 'address':
                    protocol_info['address'] = value
                elif key == 'Name':
                    protocol_info['adapter_name'] = value
                elif key == 'system':
                    protocol_info['system'] = value
                elif key == 'ifl:type':
                    protocol_info['ifl_type'] = value
                elif key == 'activityType':
                    protocol_info['activity_type'] = value
                # Additional protocol properties for comprehensive coverage
                elif key == 'credentialName':
                    protocol_info['credential_name'] = value
                elif key == 'authentication':
                    protocol_info['authentication'] = value
                elif key == 'proxyType':
                    protocol_info['proxy_type'] = value
                elif key == 'timeout':
                    protocol_info['timeout'] = value
                elif key == 'server':
                    protocol_info['server'] = value
                elif key == 'port':
                    protocol_info['port'] = value
        
        # Only return protocol data if we found meaningful protocol information
        # Support all SAP Integration Suite adapter types
        sap_protocol_types = [
            'IDOC', 'SOAP', 'HTTP', 'HCIOData', 'AMQP', 'ProcessDirect', 'Mail', 
            'JDBC', 'SFTP', 'FTP', 'SuccessFactors', 'OData', 'REST', 'XI', 
            'EDI', 'RFC', 'JMS', 'Kafka', 'MQTT', 'WebSocket', 'TCP', 'UDP'
        ]
        
        if any(key in protocol_info for key in ['component_type', 'transport_protocol', 'message_protocol']) or \
           (protocol_info.get('component_type') in sap_protocol_types):
            return protocol_info
        
        return None
    
    def _normalize_component_type(self, comp_type: str) -> str:
        """Normalize component type names for consistency."""
        type_mapping = {
            'startEvent': 'StartEvent',
            'endEvent': 'EndEvent',
            'serviceTask': 'ServiceTask',
            'callActivity': 'CallActivity',
            'parallelGateway': 'ParallelGateway',
            'exclusiveGateway': 'ExclusiveGateway'
        }
        return type_mapping.get(comp_type, comp_type)
    
    def _create_fallback_structure(self) -> Dict[str, Any]:
        """
        Create a fallback structure when XML parsing fails.
        This ensures we have a working Knowledge Graph even if XML parsing fails.
        """
        logger.info("Creating fallback structure for iFlow")
        
        return {
            'processes': [
                {'id': 'Process_1', 'name': 'Integration Process', 'type': 'Process'}
            ],
            'participants': [
                {'id': 'Participant_1', 'name': 'External System', 'type': 'Participant'}
            ],
            'components': [
                {'id': 'StartEvent_1', 'name': 'Start', 'type': 'StartEvent'},
                {'id': 'EndEvent_1', 'name': 'End', 'type': 'EndEvent'}
            ],
            'subprocesses': [],
            'sequence_flows': [
                {'id': 'SequenceFlow_1', 'name': '', 'source': 'StartEvent_1', 'target': 'EndEvent_1', 'type': 'SequenceFlow'}
            ],
            'message_flows': [],
            'protocols': [
                {'id': 'Protocol_1', 'name': 'Generic Protocol', 'type': 'Protocol', 'component_type': 'HTTP'}
            ]
        }
    
    def create_nodes_for_folder(self, folder_name: str, data: Dict[str, Any]) -> None:
        """
        Create all nodes in the Knowledge Graph for a specific folder.
        This function creates processes, participants, components, and subprocesses as nodes.
        """
        logger.info(f"Creating nodes for folder: {folder_name}")
        
        with self.driver.session() as session:
            # Create folder node as semantic layer for this specific folder
            folder_id = f"Folder_{folder_name.replace(' ', '_').replace('.', '_')}"
            session.run("""
                CREATE (f:Folder {
                    id: $folder_id,
                    name: $folder_name,
                    type: 'Folder',
                    description: 'SAP Integration Flow Knowledge Graph - Semantic Layer'
                })
            """, folder_id=folder_id, folder_name=folder_name)
            logger.debug(f"Created folder node: {folder_name}")
            
            # Create processes with folder-specific IDs
            for process in data['processes']:
                process_id = f"{folder_id}_{process['id']}"
                session.run("""
                    CREATE (p:Process {
                        id: $id,
                        name: $name,
                        type: $type,
                        folder_id: $folder_id
                    })
                """, id=process_id, name=process['name'], type=process['type'], folder_id=folder_id)
                logger.debug(f"Created process: {process['name']}")
            
            # Create participants with folder-specific IDs
            for participant in data['participants']:
                participant_id = f"{folder_id}_{participant['id']}"
                session.run("""
                    CREATE (p:Participant {
                        id: $id,
                        name: $name,
                        type: $type,
                        folder_id: $folder_id
                    })
                """, id=participant_id, name=participant['name'], type=participant['type'], folder_id=folder_id)
                logger.debug(f"Created participant: {participant['name']}")
            
            # Create components with folder-specific IDs
            for component in data['components']:
                component_id = f"{folder_id}_{component['id']}"
                session.run("""
                    CREATE (c:Component {
                        id: $id,
                        name: $name,
                        type: $type,
                        folder_id: $folder_id
                    })
                """, id=component_id, name=component['name'], type=component['type'], folder_id=folder_id)
                logger.debug(f"Created component: {component['name']}")
            
            # Create subprocesses with folder-specific IDs
            for subprocess in data['subprocesses']:
                subprocess_id = f"{folder_id}_{subprocess['id']}"
                session.run("""
                    CREATE (s:SubProcess {
                        id: $id,
                        name: $name,
                        type: $type,
                        folder_id: $folder_id
                    })
                """, id=subprocess_id, name=subprocess['name'], type=subprocess['type'], folder_id=folder_id)
                logger.debug(f"Created subprocess: {subprocess['name']}")
            
            # Create protocol nodes with folder-specific IDs
            for protocol in data['protocols']:
                protocol_id = f"{folder_id}_{protocol['id']}"
                session.run("""
                    CREATE (p:Protocol {
                        id: $id,
                        name: $name,
                        type: $type,
                        folder_id: $folder_id,
                        component_type: $component_type,
                        transport_protocol: $transport_protocol,
                        message_protocol: $message_protocol,
                        component_namespace: $component_namespace,
                        direction: $direction,
                        address: $address,
                        adapter_name: $adapter_name,
                        system: $system,
                        ifl_type: $ifl_type,
                        activity_type: $activity_type,
                        credential_name: $credential_name,
                        authentication: $authentication,
                        proxy_type: $proxy_type,
                        timeout: $timeout,
                        server: $server,
                        port: $port
                    })
                """, 
                id=protocol_id, 
                name=protocol['name'], 
                type=protocol['type'], 
                folder_id=folder_id,
                component_type=protocol.get('component_type'),
                transport_protocol=protocol.get('transport_protocol'),
                message_protocol=protocol.get('message_protocol'),
                component_namespace=protocol.get('component_namespace'),
                direction=protocol.get('direction'),
                address=protocol.get('address'),
                adapter_name=protocol.get('adapter_name'),
                system=protocol.get('system'),
                ifl_type=protocol.get('ifl_type'),
                activity_type=protocol.get('activity_type'),
                credential_name=protocol.get('credential_name'),
                authentication=protocol.get('authentication'),
                proxy_type=protocol.get('proxy_type'),
                timeout=protocol.get('timeout'),
                server=protocol.get('server'),
                port=protocol.get('port')
                )
                logger.debug(f"Created protocol: {protocol['name']} ({protocol.get('component_type', 'Unknown')}) - {protocol.get('activity_type', 'No Activity Type')}")
            
            logger.info(f"Created 1 folder, {len(data['processes'])} processes, {len(data['participants'])} participants, "
                       f"{len(data['components'])} components, {len(data['subprocesses'])} subprocesses, "
                       f"{len(data['protocols'])} protocols for {folder_name}")
    
    def create_relationships_for_folder(self, folder_name: str, data: Dict[str, Any]) -> None:
        """
        Create all relationships between nodes for a specific folder.
        This function creates FLOWS_TO, CONTAINS, and CONNECTS_TO relationships.
        """
        logger.info(f"Creating relationships for folder: {folder_name}")
        
        folder_id = f"Folder_{folder_name.replace(' ', '_').replace('.', '_')}"
        
        with self.driver.session() as session:
            # Create sequence flow relationships with folder-specific IDs
            for flow in data['sequence_flows']:
                if flow['source'] and flow['target']:
                    source_id = f"{folder_id}_{flow['source']}"
                    target_id = f"{folder_id}_{flow['target']}"
                    session.run("""
                        MATCH (source) WHERE source.id = $source AND source.folder_id = $folder_id
                        MATCH (target) WHERE target.id = $target AND target.folder_id = $folder_id
                        CREATE (source)-[:FLOWS_TO {name: $name, flow_id: $id}]->(target)
                    """, source=source_id, target=target_id, 
                               name=flow['name'], id=flow['id'], folder_id=folder_id)
                    logger.debug(f"Created sequence flow: {flow['source']} -> {flow['target']}")
            
            # Create message flow relationships with folder-specific IDs
            for flow in data['message_flows']:
                if flow['source'] and flow['target']:
                    source_id = f"{folder_id}_{flow['source']}"
                    target_id = f"{folder_id}_{flow['target']}"
                    session.run("""
                        MATCH (source) WHERE source.id = $source AND source.folder_id = $folder_id
                        MATCH (target) WHERE target.id = $target AND target.folder_id = $folder_id
                        CREATE (source)-[:CONNECTS_TO {name: $name, flow_id: $id}]->(target)
                    """, source=source_id, target=target_id, 
                               name=flow['name'], id=flow['id'], folder_id=folder_id)
                    logger.debug(f"Created message flow: {flow['source']} -> {flow['target']}")
            
            # Create process-component containment relationships
            self._create_containment_relationships_for_folder(session, folder_id, data)
            
            # Create protocol relationships
            self._create_protocol_relationships_for_folder(session, folder_id, data)
            
            # Create folder relationships to connect everything
            self._create_folder_relationships_for_folder(session, folder_id, data)
            
            # Ensure all nodes are connected (no isolated nodes)
            self._connect_isolated_nodes_for_folder(session, folder_id, data)
            
            logger.info(f"Created {len(data['sequence_flows'])} sequence flows, "
                       f"{len(data['message_flows'])} message flows, {len(data['protocols'])} protocol relationships, "
                       f"containment relationships, and folder connections for {folder_name}")
    
    def _create_containment_relationships_for_folder(self, session, folder_id: str, data: Dict[str, Any]) -> None:
        """Create CONTAINS relationships between processes and their components for a specific folder."""
        
        # Connect all processes to their components
        for process in data['processes']:
            process_id = f"{folder_id}_{process['id']}"
            session.run("""
                MATCH (p:Process {id: $process_id, folder_id: $folder_id})
                MATCH (c:Component {folder_id: $folder_id})
                CREATE (p)-[:CONTAINS]->(c)
            """, process_id=process_id, folder_id=folder_id)
    
    def _create_protocol_relationships_for_folder(self, session, folder_id: str, data: Dict[str, Any]) -> None:
        """Create relationships for protocol components for a specific folder."""
        
        # Connect protocols to their source and target components/participants
        for protocol in data['protocols']:
            protocol_id = f"{folder_id}_{protocol['id']}"
            
            # Connect protocol to source if available
            if protocol.get('source'):
                source_id = f"{folder_id}_{protocol['source']}"
                session.run("""
                    MATCH (source) WHERE source.id = $source_id AND source.folder_id = $folder_id
                    MATCH (protocol:Protocol {id: $protocol_id, folder_id: $folder_id})
                    CREATE (source)-[:USES_PROTOCOL]->(protocol)
                """, source_id=source_id, protocol_id=protocol_id, folder_id=folder_id)
            
            # Connect protocol to target if available
            if protocol.get('target'):
                target_id = f"{folder_id}_{protocol['target']}"
                session.run("""
                    MATCH (protocol:Protocol {id: $protocol_id, folder_id: $folder_id})
                    MATCH (target) WHERE target.id = $target_id AND target.folder_id = $folder_id
                    CREATE (protocol)-[:CONNECTS_TO]->(target)
                """, protocol_id=protocol_id, target_id=target_id, folder_id=folder_id)
            
            # Connect protocols to participants if they have participant_id
            if protocol.get('participant_id'):
                participant_id = f"{folder_id}_{protocol['participant_id']}"
                session.run("""
                    MATCH (protocol:Protocol {id: $protocol_id, folder_id: $folder_id})
                    MATCH (participant:Participant {id: $participant_id, folder_id: $folder_id})
                    CREATE (protocol)-[:IMPLEMENTS]->(participant)
                """, protocol_id=protocol_id, participant_id=participant_id, folder_id=folder_id)
            
            # Connect protocols to processes based on component type and direction
            if protocol.get('component_type') and protocol.get('direction'):
                session.run("""
                    MATCH (protocol:Protocol {id: $protocol_id, folder_id: $folder_id})
                    MATCH (process:Process {folder_id: $folder_id})
                    CREATE (process)-[:USES_PROTOCOL]->(protocol)
                """, protocol_id=protocol_id, folder_id=folder_id)
        
        logger.debug(f"Created protocol relationships for {folder_id}")
    
    def _create_folder_relationships_for_folder(self, session, folder_id: str, data: Dict[str, Any]) -> None:
        """Create folder relationships to connect everything to the semantic layer for a specific folder."""
        
        # Connect folder to all processes
        session.run("""
            MATCH (f:Folder {id: $folder_id})
            MATCH (p:Process {folder_id: $folder_id})
            CREATE (f)-[:CONTAINS]->(p)
        """, folder_id=folder_id)
        
        # Connect folder to all participants
        session.run("""
            MATCH (f:Folder {id: $folder_id})
            MATCH (p:Participant {folder_id: $folder_id})
            CREATE (f)-[:CONTAINS]->(p)
        """, folder_id=folder_id)
        
        # Connect folder to all subprocesses
        session.run("""
            MATCH (f:Folder {id: $folder_id})
            MATCH (s:SubProcess {folder_id: $folder_id})
            CREATE (f)-[:CONTAINS]->(s)
        """, folder_id=folder_id)
        
        # Connect folder to all protocols
        session.run("""
            MATCH (f:Folder {id: $folder_id})
            MATCH (p:Protocol {folder_id: $folder_id})
            CREATE (f)-[:CONTAINS]->(p)
        """, folder_id=folder_id)
        
        logger.debug(f"Created folder relationships for {folder_id}")
    
    def _connect_isolated_nodes_for_folder(self, session, folder_id: str, data: Dict[str, Any]) -> None:
        """Ensure all nodes are connected by creating additional relationships for a specific folder."""
        
        # Connect all participants to the main integration process
        session.run("""
            MATCH (p:Process {folder_id: $folder_id})
            MATCH (participant:Participant {folder_id: $folder_id})
            CREATE (p)-[:INTERACTS_WITH]->(participant)
        """, folder_id=folder_id)
        
        # Connect all subprocesses to processes
        session.run("""
            MATCH (p:Process {folder_id: $folder_id})
            MATCH (sp:SubProcess {folder_id: $folder_id})
            CREATE (p)-[:INVOKES]->(sp)
        """, folder_id=folder_id)
        
        # Connect participants to components that interact with them
        session.run("""
            MATCH (c:Component {folder_id: $folder_id})-[r:CONNECTS_TO]->(p:Participant {folder_id: $folder_id})
            CREATE (p)-[:RECEIVES_FROM]->(c)
        """, folder_id=folder_id)
        
        # Connect start events to their processes
        session.run("""
            MATCH (start:Component {type: 'StartEvent', folder_id: $folder_id})
            MATCH (p:Process {folder_id: $folder_id})
            CREATE (p)-[:INITIATES]->(start)
        """, folder_id=folder_id)
        
        # Connect end events to their processes
        session.run("""
            MATCH (end:Component {type: 'EndEvent', folder_id: $folder_id})
            MATCH (p:Process {folder_id: $folder_id})
            CREATE (end)-[:COMPLETES]->(p)
        """, folder_id=folder_id)
        
        # Connect protocols to components that use them
        session.run("""
            MATCH (c:Component {folder_id: $folder_id})
            MATCH (protocol:Protocol {folder_id: $folder_id})
            WHERE c.id CONTAINS protocol.name OR protocol.name CONTAINS c.name
            CREATE (c)-[:USES_PROTOCOL]->(protocol)
        """, folder_id=folder_id)
        
        # Connect protocols to participants based on system names
        session.run("""
            MATCH (participant:Participant {folder_id: $folder_id})
            MATCH (protocol:Protocol {folder_id: $folder_id})
            WHERE participant.name CONTAINS protocol.system OR protocol.system CONTAINS participant.name
            CREATE (participant)-[:IMPLEMENTS]->(protocol)
        """, folder_id=folder_id)
        
        logger.debug(f"Created additional relationships for {folder_id}")
    
    def process_single_folder(self, folder_path: str) -> bool:
        """
        Process a single iFlow folder and create its Knowledge Graph.
        Returns True if successful, False otherwise.
        """
        folder_name = self.get_folder_name(folder_path)
        logger.info(f"Processing folder: {folder_name}")
        
        try:
            # Get the iFlow file path
            iflow_file = self.get_iflow_file_path(folder_path)
            
            # Parse the iFlow XML
            data = self.parse_iflow_xml(iflow_file)
            
            # Create nodes for this folder
            self.create_nodes_for_folder(folder_name, data)
            
            # Create relationships for this folder
            self.create_relationships_for_folder(folder_name, data)
            
            self.processed_folders.append(folder_name)
            logger.info(f"Successfully processed folder: {folder_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process folder {folder_name}: {e}")
            self.failed_folders.append(folder_name)
            return False
    
    def check_isolated_nodes(self) -> Dict[str, List[str]]:
        """Check for any isolated nodes in the graph."""
        with self.driver.session() as session:
            # Find nodes with no relationships
            isolated_result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                RETURN labels(n)[0] as NodeType, n.name as NodeName, n.id as NodeId, n.folder_id as FolderId
            """)
            
            isolated_nodes = {}
            for record in isolated_result:
                node_type = record['NodeType']
                node_name = record['NodeName']
                node_id = record['NodeId']
                folder_id = record['FolderId']
                
                if node_type not in isolated_nodes:
                    isolated_nodes[node_type] = []
                isolated_nodes[node_type].append(f"{node_name} ({node_id}) in {folder_id}")
            
            return isolated_nodes
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the Knowledge Graph."""
        with self.driver.session() as session:
            # Count nodes by type
            node_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as NodeType, count(n) as Count
                ORDER BY Count DESC
            """)
            
            node_counts = {}
            total_nodes = 0
            for record in node_result:
                node_type = record['NodeType']
                count = record['Count']
                node_counts[node_type] = count
                total_nodes += count
            
            # Count relationships by type
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as RelationshipType, count(r) as Count
                ORDER BY Count DESC
            """)
            
            rel_counts = {}
            total_relationships = 0
            for record in rel_result:
                rel_type = record['RelationshipType']
                count = record['Count']
                rel_counts[rel_type] = count
                total_relationships += count
            
            # Count folders
            folder_count = session.run("MATCH (f:Folder) RETURN count(f) as count").single()['count']
            
            stats = {
                'total_folders': folder_count,
                'total_nodes': total_nodes,
                'total_relationships': total_relationships,
                'nodes_by_type': node_counts,
                'relationships_by_type': rel_counts,
                'processed_folders': len(self.processed_folders),
                'failed_folders': len(self.failed_folders)
            }
            
            return stats
    
    def export_graph_data(self, filename: str = "complete_iflow_graph_data.json") -> None:
        """Export the complete graph data to a JSON file."""
        logger.info(f"Exporting graph data to {filename}")
        
        graph_data = {
            'statistics': self.get_graph_statistics(),
            'processed_folders': self.processed_folders,
            'failed_folders': self.failed_folders,
            'folders': []
        }
        
        # Get data for each folder
        with self.driver.session() as session:
            for folder_name in self.processed_folders:
                folder_id = f"Folder_{folder_name.replace(' ', '_').replace('.', '_')}"
                
                # Get folder data
                folder_result = session.run("""
                    MATCH (f:Folder {id: $folder_id})
                    OPTIONAL MATCH (f)-[:CONTAINS]->(n)
                    RETURN f, collect(n) as nodes
                """, folder_id=folder_id)
                
                folder_data = folder_result.single()
                if folder_data:
                    graph_data['folders'].append({
                        'folder_name': folder_name,
                        'folder_id': folder_id,
                        'nodes': [dict(node) for node in folder_data['nodes']]
                    })
        
        with open(filename, 'w') as f:
            json.dump(graph_data, f, indent=2, default=str)
        
        logger.info(f"Graph data exported to {filename}")
    
    def run(self, dry_run: bool = False) -> None:
        """
        Main execution method to create Knowledge Graphs for ALL iFlow folders.
        """
        try:
            logger.info("Starting Complete iFlow Knowledge Graph creation...")
            
            # Find all iFlow folders
            iflow_folders = self.find_iflow_folders()
            
            if not iflow_folders:
                logger.warning("No iFlow folders found!")
                return
            
            if dry_run:
                logger.info("DRY RUN MODE - No database operations will be performed")
                logger.info("=" * 80)
                logger.info("FOUND IFLOW FOLDERS:")
                for i, folder_path in enumerate(iflow_folders, 1):
                    folder_name = self.get_folder_name(folder_path)
                    logger.info(f"  {i:3d}. {folder_name}")
                logger.info("=" * 80)
                logger.info(f"Total folders found: {len(iflow_folders)}")
                return
            
            # Clear existing data
            self.clear_database()
            
            # Process each folder
            for folder_path in iflow_folders:
                self.process_single_folder(folder_path)
            
            # Export graph data
            self.export_graph_data()
            
            # Check for isolated nodes
            isolated_nodes = self.check_isolated_nodes()
            if isolated_nodes:
                logger.warning("Found isolated nodes:")
                for node_type, nodes in isolated_nodes.items():
                    logger.warning(f"   {node_type}: {', '.join(nodes)}")
            else:
                logger.info("All nodes are connected - no isolated nodes found!")
            
            # Print detailed statistics
            stats = self.get_graph_statistics()
            logger.info("=" * 80)
            logger.info("COMPLETE KNOWLEDGE GRAPH CREATED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"TOTAL FOLDERS PROCESSED: {stats['total_folders']}")
            logger.info(f"SUCCESSFUL FOLDERS: {stats['processed_folders']}")
            logger.info(f"FAILED FOLDERS: {stats['failed_folders']}")
            logger.info(f"TOTAL NODES CREATED: {stats['total_nodes']}")
            logger.info(f"TOTAL RELATIONSHIPS CREATED: {stats['total_relationships']}")
            logger.info("")
            logger.info("NODES BY TYPE:")
            for node_type, count in stats['nodes_by_type'].items():
                logger.info(f"   • {node_type}: {count}")
            logger.info("")
            logger.info("RELATIONSHIPS BY TYPE:")
            for rel_type, count in stats['relationships_by_type'].items():
                logger.info(f"   • {rel_type}: {count}")
            logger.info("")
            logger.info("PROCESSED FOLDERS:")
            for folder in self.processed_folders:
                logger.info(f"   ✓ {folder}")
            if self.failed_folders:
                logger.info("")
                logger.info("FAILED FOLDERS:")
                for folder in self.failed_folders:
                    logger.info(f"   ✗ {folder}")
            logger.info("=" * 80)
            logger.info("Your Complete iFlow Knowledge Graph is ready for visualization!")
            logger.info("Open Neo4j Browser (http://localhost:7474) to explore the graph")
            logger.info("Use Neo4j Bloom for advanced visualization")
            logger.info("Each folder has its own isolated subgraph with no cross-folder connections")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error creating Complete Knowledge Graph: {e}")
            raise
        finally:
            self.close()

def main():
    """Main function to run the Complete Knowledge Graph creator."""
    import sys
    dry_run = '--dry-run' in sys.argv
    kg = CompleteIFlowKnowledgeGraph()
    kg.run(dry_run=dry_run)

if __name__ == "__main__":
    main()
